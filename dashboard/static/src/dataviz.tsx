import * as React from 'react';
import { DonutChart, IDonutChartProps, IChartProps, IChartDataPoint } from '@uifabric/charting';
import { DefaultPalette } from 'office-ui-fabric-react/lib/Styling';

export interface IDataVizProps {
  totag: number;
  tagged: number;
  tagging: number;
}
 
export class DataViz extends React.Component<IDataVizProps, {}> {
  public render() {
    const points: IChartDataPoint[] = [
      { legend: 'To tag', data: this.props.totag, color: DefaultPalette.orangeLighter },
      { legend: 'Tagging', data: this.props.tagging, color: DefaultPalette.purpleLight },
      { legend: 'Tagged', data: this.props.tagged, color: DefaultPalette.greenLight }
    ];

    const data: IChartProps = {
      chartData: points
    };
    return <DonutChart data={data} innerRadius={0} />;
  }
} 

