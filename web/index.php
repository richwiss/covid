<html>
  <head>
    <title>Covid-19 Graphs for PA</title>   
    <link rel="stylesheet" type="text/css" href="mystyle.css">
  </head>
  <body>
    <h1>Covid-19 Graphs for PA</h1>
    <h3>Data Last Updated:  <?php
echo date('l F d, Y \a\t H:i:s', filemtime("/home/richardw/Dropbox/covid/COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"));
?> 
</h3>
    <table class="serif">
      <thead>
        <tr>
          <th>State</th>
          <th>Region</th>
          <th>County</th>
          <th>New Cases</th>
          <th>Trend</th>
          <th>Yellow Target</th>
        </tr>
      </thead>
      <tbody>
        <?php include 'table.html';?>
      </tbody>
    </table>

    <h4>
      <p>
	Data from the <a href="https://github.com/CSSEGISandData/COVID-19">JHU CSSE COVID-19 Dataset</a> and <a href="https://www.census.gov/data/datasets/time-series/demo/popest/2010s-counties-total.html">the US Census Bureau</a>.<BR />
      Source code and data available from <a href="https://github.com/richwiss/covid">github</a>. Pull requests and comments welcome.<BR /> 
	Created by <a href="https://twitter.com/richwiss/">@richwiss</a>
      </p>
  </body>
</html>
