# Efficient hyperparameter tuning

The goal of this thesis is to research hyperparameter optimization with limited resources and perform a comparison of the algorithms. We carried out experiments on tabular benchmarks and real-world tasks, where we compare the state-of-the-art algorithms. This repository is divided into two parts: code for running the experiments, and code for the analysis of the results.

## 1. Running the experiments

We used the syne-tune library for running the experiments and logging the results. 

### How-to

1. Install Python 3.10.11

2. Install requirements_st.txt, preferably into a virtual environment.

3. Activate the virtual environment.

4. Preparing the datasets
   
   a) SVHN should download the data automatically.
   
   b) CIFAR-10 requires manual download from the [source](https://www.cs.toronto.edu/~kriz/cifar.html) into the data/cifar10 directory.
   
   c) ChestX-ray14 requires manual download, follow the instructions of the dataset class, which can be found from the load_data.py script.
   
   d) PTB-XL requires downloading of the dataset and preprocessing. Download the dataset from [physionet.org](https://physionet.org/content/ptb-xl/1.0.3/) into the data/ptbxl/ directory. Install the wfdb library and run the src/datasets/ptbxl.py file.

5. Real-world experiments are launched using the run_hpo_synetune.py script from the repository base directory.
   
   - Example: `python src/run_hpo_synetune.py --experiment_tag "test-1" --experiment_definition "cifar-simple" --method "ASHA" --num_seeds 30 --master_seed 40 --n_workers 1`

6. Tabular experiments are launched by running the the hpo_main.py code located in the src/tabular_exp directory
   
   * before launching tabular experiments, make sure you have full syne-tune instalation that contains tabular benchmarks, too. If you have any issues regarding the installation of syne-tune, please refer to the syne-tune library documentation. 
   
   * Example: `python src/tabular_exp/hpo_main.py --experiment_tag "test-1" --benchmark "lcbench-christine" --num_seeds 10 --n_workers 1 --method 'RS'`
   
   With these two commands and substitution for all the `--method` and `--experiment_definition` pairs, it is possible to replicate the experiments from the thesis, up to a randomness in the process uncontrollable by setting the seed. We have used 30 seeds for tabular, and 10 seeds for real-world experiments. The experiment definition names are same as the experiment names used in the thesis. List of methods is provided in the Algorithms section of this document.

Note that the repository also contains deprecated code that used multiple other libraries (e.g. Optuna, SMAC) instead of Syne-tune. The launching script is `run_hpo.py`, but it was not updated to the latest changes in experiment definitions. We include the requirements.ot.txt file for experimens with these libraries. 

## 2. Analysis of the data

We analyze the data and plot the results in Jupyter Notebooks. For experimenting with the notebooks, you will need to setup the environment as for running the Syne-tune experiments. Therefore, you need Python 3.10.11 installation with the packages from requirements_st.txt.

**Real-world experiments**

The notebook for analysis of the real-world experiments is the `notebooks/real_benchmarks/real_analysis.ipynb`.

We include the pre-processed data from the experiments in the results directory, too. Therefore, it is possible to run the notebook and re-create all plots and tables we used in the thesis.

**Tabular experiments**

The notebooks for analysis of tabular experiments are in the `notebooks/tabular_benchmarks` directory. We used two notebooks - `aggregate_results.ipynb` for the statistical analysis, critical diagram, and other aggregated results, and `cumulative.ipynb` for the plots using the cumulative regret common metric.

# Experiments

Here, we briefly summarize the experiments.

## Real-world experiments

Experiments are performed on several datasets, that include:

* CIFAR-10 image classification dataset

* SVHN image classification dataset

* PTB-XL dataset, ECG -> diagnosis

* ChestX-ray14, xRay -> diagnosis

For the PTB-XL dataset, we have pre-processed the data and created the dataset.

### Tabular experiments

We also perform experiments on these tabular benchmarks:

* NAS-Bench-201

* FCNet

* LCBench

These benchmarks are included in the syne-tune library. We did not use all tasks from the LCBench. We used only the following datasets from LCBench: Fashion-MNIST, airlines, albert, christine, covertype, dionis, helena, higgs.

### Algorithms

We perform the comparison on these algorithms:

* Random search

* ASHA

* BOHB

* DEHB

* HyperBand

* MOBSTER

* HyperTune

* DyHPO

Unfortunately, we used different naming schemes for the tabular experiments and for the real-world experiments. We provide the strings of the methods for tabular experiments here: "RS", "ASHA", "MOBSTER-JOINT", "HYPERTUNE-INDEP", "SYNCHB", "BOHB", "DyHPO", "DEHB".

And the strings for real-world benchmakrs are:  "RS", "ASHA", "DEHB", "BOHB", "DyHPO", "MOBSTER", "HyperTune".