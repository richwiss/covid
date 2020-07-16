# COVID-19 Plots

The initial version of these tools helps visualize Pennsylvania's progress towards controlling SARS-CoV-2, the virus that causes COVID-19 (Coronavirus disease 2019).

The included python program requires numerous Python libraries: `pandas`, `matplotlib`, `seaborn`, `numpy`, and `tqdm`. (TODO: `requirements.txt`)

Sources:
* Pennsylvania-specific region designations come from [Governor Tom Wolf's Process to Reopen Pennsylvania](https://www.governor.pa.gov/process-to-reopen-pennsylvania/). A [copy of the relevant map](resources/20200423-Bureau-Community-Health-Systems-Regional-Map-Opt.png) is available in this project.
* The [current phase of various counties](phases.csv) is required by this project. (TODO: Make this optional)
* A [region description file](resources/regions.csv) that maps counties to larger regions is required. (TODO: Make this optional)
* Population data and COVID-19 data comes from the [JHU CSSE COVID-19 Dataset](https://github.com/CSSEGISandData/COVID-19). A local copy of the JHU repository is required by this project.


Requirements:
* pandas
* matplotlib
* seaborn
* numpy
* tqdm
* plotly
    * Requires electron, orca
    * npm install -g electron@6.1.4 orca  (omit -g to install in user directory)
