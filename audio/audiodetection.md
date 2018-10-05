# Audio Detection using Audioset & Audio Analysis

## Active Learning + Audio Detection

The detection of audio and classification of sounds are currently green field research areas with limited resources and best practices. The labeling of audio, augmentation and model generation are essential for building Computer Audio Detection projects. Recent strides in the space such as the development of large scale datasets with labeled sound clips (Audioset, Freesound) and the classification models around those datasets are providing the ML space best practice parity with common Computer Vision and image labeling techniques. In this section of Active Learning we will explore beneficial practices, and ML pipeline techniques around audio augmentation, audio labeling, & sound classification to automate the detection of sounds for Human annotators. To begin, we leverage the Audioset Dataset to build base line tensorflow models to detect sounds in our custom dataset. 

## Environment Setup

Use a local machine or a Data Science VM with GPUs. Our team leveraged the [Azure Data Science Virtual Machine](https://azure.microsoft.com/en-us/services/virtual-machines/data-science-virtual-machines/) from the Azure Marketplace. Any reasonably recent version of these packages should work. TensorFlow should be at least version 1.0. We have tested with Python 2.7.6 and 3.4.3 on an Ubuntu-like system with NumPy v1.13.1, SciPy v0.19.1, resampy v0.1.5, TensorFlow v1.2.1, and Six v1.10.0.


**Azure Data Science VM (Linux)**

* Python - 3.5.5	N/A
* Numpy - 1.14.5
* Scipy - 1.1.0
* Resampy - 0.2.1
* Tensorflow-GPU - 1.10.0
* Six - 1.11.0


### Enabling GPU Device

If you have a different GPU / OS please go to [official website](https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1710/x86_64/) and find the appropriate driver.

This command can help with find information on your GPU:

```
sudo lshw -C display
```

First, install the latest version of Docker:

```
$ sudo apt-get update
$ sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
$ sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
$ sudo apt-get update
$ sudo apt-get install docker-ce
```

To install CUDA drivers for Ubuntu 16.04 for NVIDIA Tesla k80:

```
$ wget http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-repo-ubuntu1604_8.0.44-1_amd64.deb
$ sudo dpkg -i cuda-repo-ubuntu1604_8.0.44-1_amd64.deb
$ sudo apt-get update
$ sudo apt-get -f install
$ sudo apt-get install cuda
```

nvidia-smi is NVIDIA's System Management Interface. It provides a command line utility that allows monitoring and management capabilities for NVIDIA devices. 

To install nvidia-docker and test nvidia-smi:

```
$ sudo apt-get install nvidia-docker2
$ sudo nvidia-docker run --rm nvidia/cuda nvidia-smi
```
> **NOTE**: A VM restart may be required for packages to be fully installed.

Example output:

```
Wed Sep 26 21:17:23 2018
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 410.48                 Driver Version: 410.48                    |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  Tesla K80           Off  | 00006DE9:00:00.0 Off |                    0 |
| N/A   40C    P0    83W / 149W |      0MiB / 11441MiB |      1%      Default |
+-------------------------------+----------------------+----------------------+

+-----------------------------------------------------------------------------+
| Processes:                                                       GPU Memory |
|  GPU       PID   Type   Process name                             Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+
```


### Environment Testing Set Up 

``` sh
# You can optionally install and test VGGish within a Python virtualenv, which
# is useful for isolating changes from the rest of your system. For example, you
# may have an existing version of some packages that you do not want to upgrade,
# or you want to try Python 3 instead of Python 2. If you decide to use a
# virtualenv, you can create one by running
#   $ virtualenv vggish   # For Python 2
# or
#   $ python3 -m venv vggish # For Python 3
# and then enter the virtual environment by running
#   $ source vggish/bin/activate  # Assuming you use bash
# Leave the virtual environment at the end of the session by running
#   $ deactivate
# Within the virtual environment, do not use 'sudo'.
# Upgrade pip first.
$ sudo python -m pip install --upgrade pip
# Install dependences. Resampy needs to be installed after NumPy and SciPy
# are already installed.
$ sudo pip install numpy scipy
$ sudo pip install resampy tensorflow six
# Clone TensorFlow models repo into a 'models' directory.
$ git clone https://github.com/tensorflow/models.git
$ cd models/research/audioset
# Download data files into same directory as code.
# These files are used for the VGG inferencing to convert audio wav files to a spectogram supported by the Audioset model we generate.
$ curl -O https://storage.googleapis.com/audioset/vggish_model.ckpt
$ curl -O https://storage.googleapis.com/audioset/vggish_pca_params.npz
# Installation ready, let's test it.
$ python vggish_smoke_test.py
# If we see "Looks Good To Me", then we're all set.
```
> From <https://github.com/tensorflow/models/tree/master/research/audioset> 

## Custom Audio Conversion

Here we will take a custom wav file and extract the audio feature embeddings through a VGGish inference. VGGish is the 128-dimension embeddings specifically found in Audioset which was trained on millions of youtube videos. A tensorflow record with the embeddings are outputted to a directory and you can use this to pass into your own model. For more on VGGish check out this [paper](https://arxiv.org/pdf/1609.09430.pdf). Here's what you need:

-  A WAV file (assumed to contain signed 16-bit PCM samples) 

    * This wav file is converted into log mel spectrogram examples, fed into VGGish, the raw embedding output is whitened and quantized, and the postprocessed embeddings are optionally written in a SequenceExample to a TFRecord file (using the same format as the embedding features released in AudioSet).
	* Size of the file - The VGG inference script Converts audio waveform into an array of examples for VGGish. So whichever size your training data set is based on. For audioset this is 10 seconds.

	    - Input: data: np.array of either one dimension (mono) or two dimensions(multi-channel, with the outer dimension representing channels). Each sample is generally expected to lie in the range [-1.0, +1.0], although this is not required.

		- Output: 3-D np.array of shape [num_examples, num_frames, num_bands] which represents a sequence of examples, each of which contains a patch of log mel spectrogram, covering num_frames frames of audio and num_bands mel frequency bands, where the frame length is vggish_params.STFT_HOP_LENGTH_SECONDS.

- Converting to .WAV 16-bit PCM Sample
	- Audio Samples
		- I am using 2 audio samples for gunshots provided by freesound.org
			- Sample 1 - https://freesound.org/people/watupgroupie/sounds/36815/
			- Sample 2 - https://freesound.org/people/fastson/sounds/399065/
	- Converting WAV 16bit signed PCM
		- [Online-Convert](https://www.online-convert.com)
			- No changes in the sampling rate
			- No Changes to the audio channel
			- In advanced options select the following as your PCM format PCM 16bit signed Small Endian
				- Sample 1 - https://rtwrt.blob.core.windows.net/post5-audioset/samples/sample1_16bit_PCM_signed_smallendian.wav
				- Sample 2 - https://rtwrt.blob.core.windows.net/post5-audioset/samples/sample2_16bit_PCM_signed_smallendian.wav


|   Clip   | Converter       |  Channel  | Sample Rate | Endian  | PCM-16bit| Signed |
| -------- |:---------------:| ---------:|-----------: |---------| ---------| -------|
| Clip | Online-Converter| No-Change | No-Change   | Small    | Yes      | Yes    |
| Clip2 | Online-Converter| No-Change | No-Change   | Small     | Yes      | Yes    |

>  Upload to a cloud storage like Azure Blob & curl your files:
> `curl -O https://rtwrt.blob.core.windows.net/post5-audioset/samples/sample1_16bit_PCM_signed_smallendian.wav` 

## VGG Conversion Tester

Use vggish_inference_demo.py to create a VGG analysis of your custom wave file in a tensor flow record. Specify the path to the wav file  and the output path of where you want the tfrecord to be generated.

`python vggish_inference_demo.py --wav_file clip2-02_16bit_PCM_signed_smallendian.wav \
                                    --tfrecord_file tfrecrods/new2 \
                                    --checkpoint /path/to/model/checkpoint \
                                    --pca_params /path/to/pca/params`
                                    
> Due to an outdated version of audioset leveraging the video_id parameter, replace your file with the [vgg_inference_demo.py](vgg_inference_demo.py) we provided. We added a context property that appends a video_id property based on the name of the wav file inputted.


## Selection of model:

* **Video-Level Models**
	- `LogisticModel`: Linear projection of the output features into the label space, followed by a sigmoid function to convert logit values to probabilities.
	- `MoeModel`: A per-class softmax distribution over a configurable number of logistic classifiers. One of the classifiers in the mixture is not trained, and always predicts 0.
* **Frame-Level Models**
	- `LstmModel`: Processes the features for each frame using a multi-layered LSTM neural net. The final internal state of the LSTM is input to a video-level model for classification. Note that you will need to change the learning rate to 0.001 when using this model.
	- `DbofModel`: Projects the features for each frame into a higher dimensional 'clustering' space, pools across frames in that space, and then uses a video-level model to classify the now aggregated features.
	- `FrameLevelLogisticModel`: Equivalent to 'LogisticModel', but performs average-pooling on the fly over frame-level features rather than using pre-aggregated features.

> From <https://github.com/google/youtube-8m#overview-of-models> 

## Audioset Ontology 

```
Firearm
{	
    "id": "/m/032s66",
    "name": "Gunshot, gunfire",
    "description": "The sound of the discharge of a firearm, or multiple such discharges.",
    "citation_uri": "http://en.wikipedia.org/wiki/Gunshot",
    "positive_examples": ["youtu.be/--PG66A3lo4?start=80&end=90", "youtu.be/PKEhOxE-Ovs?start=130&end=140", "youtu.be/c9030y4sJo0?start=140&end=150", "youtu.be/6slrju_ar9U?start=290&end=300", "youtu.be/K1cnDXbkPu0?start=170&end=180", "youtu.be/AjIQf3HK_Vc?start=130&end=140", "youtu.be/klCJfirqUF8?start=30&end=40", "youtu.be/Ma65O2T_hN0?start=10&end=20", "youtu.be/-Ho5tDtuah0?start=50&end=60"],
    "child_ids": ["/m/04zjc", "/m/02z32qm", "/m/0_1c", "/m/073cg4"],
    "restrictions": []
    },
```
> From <https://github.com/audioset/ontology/blob/master/ontology.json> 

## Dataset Ingestion & Sample Models

1. Download the Audioset feature embeddings dataset in a tar file and unpack the tar.
    - Download using `curl -O storage.googleapis.com/us_audioset/youtube_corpus/v1/features/features.tar.gz`
    - Unpack using `tar -xzf features.tar.gz`
2. Clone the youtube8m repository - `git clone https://github.com/google/youtube-8m.git`
> **Learnings**: Audioset uses an outdated version of the youtube 8m model templates and requires a change in the readers.py file. Our team changed all instances of `id` to `video_id` and also edited the hard coded number fo classes from 3826 to 527 (The current number of Audioset class). Refer to [readers.py](readers.py)

## Building a Model

### Train

Now that you have the Youtube-8m model samples and the audioset features to train the model lets now train an frame-level model `LstmModel` on our audio embedding features. Run the command below where"
- `--train_data_pattern` is the path to the balanced_train tensorflow records for the audioset embeddings
- `--train_dir` is an arbitrary path to a directory where the model will be creates
- `--base_learning_rate` is set to 0.001 since we are using an LSTM Model
- `--num_epochs` is an arbitrary number for the amount of times the model will be trained on the dataset. Ideally we would like to have a 0.01 loss so train the model long enough so the loss value is relatively close to this. *try not to overfit the model*

`python youtube-8m/train.py --frame_features --model=LstmModel --feature_names=audio_embedding --feature_sizes=128 --train_data_pattern=audioset_v1_embeddings/bal_train/*.tfrecord --train_dir model_new/dir --start_new_model --base_learning_rate=0.001 --num_epochs=1500`
#### Tracking Training
* You can use **Nohup** to write the console to a txt and monitor the loss
    * Use `nohup python youtube-8m/train.py --frame_features --model=LstmModel --feature_names=audio_embedding --feature_sizes=128 --train_data_pattern=audioset_v1_embeddings/bal_train/*.tfrecord --train_dir model_new/dir --start_new_model --base_learning_rate=0.001 --num_epochs=1500 &`
    * Then open another terminal and monitor the loss using `tail -f nohup.out`
* You can also use **Tensorboard** to monitor the model loss and other metrics using a UI.
    * In the portal add port `6006` as an inbound rule for your network security group that you VM is configured to.
    * Use `tensorboard --logdir=model_new --host=0.0.0.0` from a new terminal in the VM and navigate to tensorboard by entering `<Public_Ip_Address_for_your_VM>:6006`

### Evalute

You can now use the binaries for evaluating Tensorflow models on the YouTube-8M dataset with audioset embeddings. Run this command once or for an arbitrary time:

* `--train_data_pattern` is the path to the eval_train tensorflor wecords for the audtioset embeddings
* `--train_dir` is the path to the previousl created directory for your model

`python youtube-8m/eval.py --eval_data_pattern=features/audioset_v1_embeddings/eval/*.tfrecord --train_dir model_new/dir`

### Inference

Now that you have a working model you can run 3 commands to evaluate how our model scores audio based on the audio embedding features.

First we'll run an inference on our bal_train dataset. These are audio records that our model was built using. Run the command where:
- `--top_k` is the top 3 labels tagged by the model
- `--input_data_pattern` is a partition of some of the tfrecords for us to evaluate the model scores. In this example we use all tfrecords with a*
- `--output_file` is a user defined path to the output csv file the model generates with the scores.

`python youtube-8m/inference.py --output_file Bal_SamplePredictions.csv --input_data_pattern=features/audioset_v1_embeddings/bal_train/a*.tfrecord --train_dir model_new/dir --top_k=3`

With the output csv file use [Bal_Train_Segments.csv](http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/balanced_train_segments.csv) to validate that the video files were correctly labeled. Repeat this inference step replacing the `input_data_pattern` with the Unbalance_Data and then with the output tfrecord that is created with a custom wav file.
> The Balance_Train dataset scores should be very accurate since we used this data to train the LstmModel. The Unbalnced_Train dataset will be a bit less accurate and your custom audio tfrecord for a user wav file will vary based on a variety of variables that will need to be further explored.
