import * as React from 'react';
import { DataViz } from './dataviz';
import axios from 'axios';
import './activelearningstatistics.css';

export interface IActiveLearningStatisticsState {
  totag: number;
  tagging: number;
  count: number;
  tagged: number;
}

export class ActiveLearningStatistics extends React.Component<{}, IActiveLearningStatisticsState> {
  constructor(props: {}) {
    super(props);
    this.state = {
      totag: 0,
      tagging: 0,
      tagged: 0,
      count: 0
    }
  }
  refreshData = () => {
    axios.get('/stats').then(response => {
      console.log(response.data);
      this.setState({
        totag: response.data.totag,
        tagging: response.data.tagging,
        tagged: response.data.tagged,
        count: response.data.count
      })
    });
  }

  componentDidMount() {
    this.refreshData();
    window.setInterval(this.refreshData, 10000);
  }
  public render() {
    return (
    <div>
      <h2 className={'title'}>Active learning detect statistics</h2>
      <div className={'title'}>Total images uploaded: {this.state.count}</div>
      <div className={'title'}>Images to tag: {this.state.totag}</div>
      <div className={'title'}>Tagging images: {this.state.tagging}</div>
      <div className={'title'}>Tagged images: {this.state.tagged}</div>
      <div className={'chart'}>
        <DataViz totag={this.state.totag} tagged={this.state.tagged} tagging={this.state.tagging} />
      </div>
    </div>);
  }
} 

