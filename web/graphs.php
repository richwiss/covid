<html>
  <head>
    <title>Covid-19 Graphs</title>   
    <link rel="stylesheet" type="text/css" href="../../mystyle.css">
  </head>
  <script type="text/javascript">window.PlotlyConfig = {MathJaxConfig: 'local'};</script>
        <script src="https://wicentowski.com/covid/plotly.min.js"></script>    
  <body>
    <?php
      if (isset($_GET['location'])) {
         $location=$_GET['location'];
      } else {
         $location="Delaware_County_Pennsylvania";
      }
      ?>
    <table class="serif">
      <tbody>
        <tr>
          <td><?php $url = $location . '_new_cases.html'; include $url;?></td>
          <td><?php $url = $location . '_yellow_target.html'; include $url;?></td>
       </tr>
       <tr>
          <td><?php $url = $location . '_trend.html'; include $url;?></td>
          <td><?php $url = $location . '_posneg.html'; include $url;?></td>
       </tr>
      </tbody>
    </table>

    <h4>
      <p>
	Data from the <a href="https://github.com/CSSEGISandData/COVID-19">JHU CSSE COVID-19 Dataset</a> and the <a href="https://www.census.gov/data/datasets/time-series/demo/popest/2010s-counties-total.html">US Census Bureau</a>.<BR />
      Source code and data available from <a href="https://github.com/richwiss/covid">github</a>. Pull requests and comments welcome.<BR /> 
	Created by <a href="https://twitter.com/richwiss/">@richwiss</a>
      </p>
  </body>
</html>
