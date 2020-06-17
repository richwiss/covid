<html>
  <head>
    <title>Covid-19 Graphs</title>   
    <link rel="stylesheet" type="text/css" href="../../mystyle.css">
  </head>
  <body>
    <h1>Covid-19 Graphs</h1>
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
      <p>Data updated:  <?php
			  echo date('l F d, Y \a\t H:i:s', filemtime("/home/richardw/Dropbox/covid/COVID-19/csse_covid_19_data/csse_covid_19_time_series/")); ?><BR />
      Table updated:  <?php
			   echo date('l F d, Y \a\t H:i:s', filemtime("index.php")); ?>
      </p>	
      <p>
	Data from the <a href="https://github.com/CSSEGISandData/COVID-19">JHU CSSE COVID-19 Dataset</a> and the <a href="https://www.census.gov/data/datasets/time-series/demo/popest/2010s-counties-total.html">US Census Bureau</a>.<BR />
      Source code and data available from <a href="https://github.com/richwiss/covid">github</a>. Pull requests and comments welcome.<BR /> 
	Created by <a href="https://twitter.com/richwiss/">@richwiss</a>
      </p>
    </h4>
    <h4>
      </p>
      
    </h4>
    
  </body>
</html>
