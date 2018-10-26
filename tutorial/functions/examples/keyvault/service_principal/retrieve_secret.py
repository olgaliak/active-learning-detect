import logging
import os

import azure.functions as func
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.common.credentials import ServicePrincipalCredentials

def get_config_from_environment():
    config = {}
    config_base = os.environ.get('APPLICATION_PREFIX', None)
    if config_base is None:
        logging.error('APPLICATION_PREFIX must be set')
        return None
    config['client_id'] = os.environ.get(config_base + '_ID', None)
    config['client_secret'] = os.environ.get(config_base + '_PASSWORD', None)
    config['tenant_id'] = os.environ.get(config_base + '_TENANT_ID', None)
    if config['client_id'] is None or config['client_secret'] is None or config['tenant_id'] is None:
        logging.error(config_base + '_ID, ' + config_base + '_PASSWORD, ' + config_base + '_TENANT_ID must all be set.')
        return None
    config['keyault_uri'] = os.environ.get('KEYVAULT_URI', None)
    if config['keyault_uri'] is None:
        logging.error('KEYVAULT_URI must be set')
        return None
    config['storage_account_kv_base'] = os.environ.get('STORAGE_ACCOUNT_KV_BASE', None)
    if config['storage_account_kv_base'] is None:
        logging.error('STORAGE_ACCOUNT_KV_BASE must be set')
        return None
    return config

def retrieve_keyvault_client(config):
    # create the service principle credentials used to authenticate the client
    credentials = ServicePrincipalCredentials(client_id=config['client_id'],
                                              secret=config['client_secret'],
                                              tenant=config['tenant_id'])
    # create the client using the created credentials
    client = KeyVaultClient(credentials)
    return client

def retrieve_storage_account_info(config):
    client = retrieve_keyvault_client(config)
    vaultUri = config['keyault_uri']
    saNameKey = config['storage_account_kv_base'] + '_name'
    saValueKey = config['storage_account_kv_base'] + '_name'
    logging.error('Vault ' + vaultUri + ', name key: ' + saNameKey + ', value key: ' + saValueKey)
    sa_name_bundle = client.get_secret(config['keyault_uri'], config['storage_account_kv_base'] + '_name', secret_version="")
    sa_key_bundle = client.get_secret(config['keyault_uri'], config['storage_account_kv_base'] + '_key', secret_version="")
    return sa_name_bundle, sa_key_bundle
    
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Retrieve secret from Azure Keyvault.')

    config = get_config_from_environment()
    if config is None:
        return func.HttpResponse(
             "Configuration incorrect",
             status_code=503
        )

    name, key = retrieve_storage_account_info(config)
    return func.HttpResponse(f"Got {name}, {key}")