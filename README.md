# COVID-19 Plots

The initial version of these tools helps visualize Pennsylvania's progress towards controlling SARS-CoV-2, the virus that causes COVID-19 (Coronavirus disease 2019).

The included Jupyter notebook requires numerous Python libraries: `pandas`, `matplotlib`, `seaborn`, `numpy`, and `tqdm`.

Sources:
* Pennsylvania-specific region designations come from [Governor Tom Wolf's Process to Reopen Pennsylvania]
(https://www.governor.pa.gov/process-to-reopen-pennsylvania/). A [copy of the relevant map](resources/20200423-Bureau-Community-Health-Systems-Regional-Map-Opt.png) is available in this project.
* The [current phase of each county in Pennsylvania](phases.csv) is required by this project.
* Population data comes from [the United States Census Bureau](https://www.census.gov/data/datasets/time-series/demo/popest/2010s-counties-total.html). A [copy of the census data](resources/co-est2019-annres.xlsx) is available in this project. 
* A [modified version of the population data](resources/county-populations.csv) that only includes population data from 2019 and is supplemented with the regional designations for Pennsylvania is required by this project.
* COVID-19 data comes from the [JHU CSSE COVID-19 Dataset](https://github.com/CSSEGISandData/COVID-19). A local copy of the JHU repository is required by this project.



