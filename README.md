# Efficient hyperparameter tuning

This is the repository for the Efficient hyperparameter tuning thesis. As a part of the thesis, we carried out experiments on tabular benchmarks and real-world tasks, which are used to analyse and compare state-of-the-art algorithms. Therefore, there are two key components in this repository: code for running the experiments, and code for the analysis of the results.

## 1. Running the experiments

We used the syne-tune library for running the experiments and logging the results. By default, the results are logged into the syne-tune directory, which will be located in the home directory.

### How-to

1. Install Python 3.10.11

2. Install `requirements_st.txt`, preferably into a virtual environment, and activete the virtual environment

3. Prepare the dataset needed for the experiment:
   
   a) SVHN should download the data automatically,
   
   b) CIFAR-10 requires manual download from the [source](https://www.cs.toronto.edu/~kriz/cifar.html) into the `data/cifar10` directory,
   
   c) ChestX-ray14 requires manual download, follow the instructions of the dataset class, which is in the `src/datasets/torchxrayvision.py` file, and load the files into the `data/NIH directory`,
   
   d) PTB-XL requires downloading of the dataset and preprocessing. Download the dataset from [physionet.org](https://physionet.org/content/ptb-xl/1.0.3/) into the `data/ptbxl` directory. Install the wfdb library and run the src/datasets/ptbxl.py file.

4. Real-world experiments are launched using the run_hpo_synetune.py script from the repository base directory.
   
   - Example: `python src/run_hpo_synetune.py --experiment_tag "test-1" --experiment_definition "cifar_simple" --method "ASHA" --num_seeds 10 --master_seed 40 --n_workers 1`
   - Note that real-world experiments have an usual runtime in hours per one repetiton, and some could take more than a day on a GPU.

5. Tabular experiments are launched by running the the hpo_main.py code located in the src/tabular_exp directory
   
   * before launching tabular experiments, make sure you have full syne-tune instalation that contains tabular benchmarks, too. If there are any issues regarding the installation of syne-tune or tabular benchmarks, please refer to the syne-tune library documentation. 
   
   * Example: `python src/tabular_exp/hpo_main.py --experiment_tag "test-1" --benchmark "lcbench-christine" --num_seeds 30 --n_workers 1 --method 'RS'`

It is possible to re-run the experiments from the thesis by running these two scripts with different parameters. More precisely, for all the `--method` and `--experiment_definition` pairs. We used 30 seeds for tabular benchmarks, starting at the default value, and 10 seeds for the real-world experiments, starting at master_seed=40 up to 49.

The **experiment definition** names are same as the experiment names used in the thesis for the tabular benchmarks. For real-world experiments, the experiment definitons are exactly the names of the subdirectories in the `experiment_definitions` directory. List of algorithms is provided in the Algorithms section of this document.

Note that the repository also contains deprecated code that used multiple other libraries (e.g. Optuna, SMAC) instead of Syne-tune. The launching script is `run_hpo.py`, but it was not updated to the latest changes in experiment definitions. We include the requirements_ot.txt file for experimens with these libraries. 

## 2. Analysis of the data

We analyze the data and plot the results in Jupyter Notebooks. For experimenting with the notebooks, you can use the syne-tune setup, but the syne-tune library, as well as many others, is not needed.

We include the collected data necessary for reproduction of the analysis and plots in the `results` directory. There is a separate file for the tabular experiments, and another file for the real-world experiments.

**Real-world experiments**

The notebook for analysis of the real-world experiments is the `notebooks/real_benchmarks/real_analysis.ipynb`.

The notebook already contains code for loading the data.

**Tabular experiments**

The notebooks for analysis of tabular experiments are in the `notebooks/tabular_benchmarks` directory. We used two notebooks for the analysis - `aggregate_results.ipynb` for the statistical analysis, critical diagram, and other aggregated results, and `cumulative.ipynb` for the plots using the cumulative regret common metric. There is also the `serialize_tabular.ipynb` notebook that we used to save the collected data.

# Experiments

Here, we briefly summarize the experiments.

## Real-world experiments

There were 7 real world experiments. Experiments are performed on several datasets that include:

* CIFAR-10 image classification dataset

* SVHN image classification dataset

* PTB-XL dataset, ECG -> diagnosis classification

* ChestX-ray14, xRay images -> diagnosis classification

For the PTB-XL dataset, pre-processing of the raw data is needed.

### Tabular experiments

We also perform experiments on these tabular benchmarks:

* NAS-Bench-201

* FCNet

* LCBench

These benchmarks are included in the syne-tune library. We did not use all tasks from the LCBench. We used only the following datasets from LCBench: Fashion-MNIST, airlines, albert, christine, covertype, dionis, helena, higgs. In total, there were 15 experiments with 8 algorithms. All experiments should finish within several days of CPU time in total.

### Algorithms

We perform the comparison of these algorithms:

* Random search

* ASHA

* BOHB

* DEHB

* HyperBand

* MOBSTER

* HyperTune

* DyHPO

Unfortunately, we used different naming schemes for the tabular experiments and for the real-world experiments. We provide the strings of the methods for tabular experiments here: "RS", "ASHA", "MOBSTER-JOINT", "HYPERTUNE-INDEP", "SYNCHB", "BOHB", "DyHPO", "DEHB".

The strings for real-world benchmakrs are: "RS", "ASHA", "BOHB", "DyHPO", and "HyperTune".  "DEHB" and "MOBSTER" are available too, even though we did not run the experiments with these two algorithms.