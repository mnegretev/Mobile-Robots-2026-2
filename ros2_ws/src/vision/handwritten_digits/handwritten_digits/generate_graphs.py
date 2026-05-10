import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def load_results(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_graphs(results, title_prefix, output_prefix):
    # Group by parameters
    param_groups = defaultdict(list)
    for result in results:
        config = result['config']
        key = (config['learning_rate'], config['epochs'], config['batch_size'])
        param_groups[key].append(result['metrics']['accuracy'])

    # Parameters
    learning_rates = sorted(set(k[0] for k in param_groups.keys()))
    epochs_list = sorted(set(k[1] for k in param_groups.keys()))
    batch_sizes = sorted(set(k[2] for k in param_groups.keys()))

    # Plot 1: Accuracy vs Learning Rate (averaged over other params)
    lr_accuracy = defaultdict(list)
    for (lr, ep, bs), accs in param_groups.items():
        lr_accuracy[lr].extend(accs)
    avg_lr_acc = {lr: np.mean(accs) for lr, accs in lr_accuracy.items()}
    plt.figure(figsize=(10, 6))
    plt.plot(list(avg_lr_acc.keys()), list(avg_lr_acc.values()), marker='o')
    plt.xlabel('Learning Rate')
    plt.ylabel('Average Accuracy')
    plt.title(f'{title_prefix} - Accuracy vs Learning Rate')
    plt.grid(True)
    plt.savefig(f'{output_prefix}_accuracy_vs_lr.png')
    plt.close()

    # Plot 2: Accuracy vs Epochs
    ep_accuracy = defaultdict(list)
    for (lr, ep, bs), accs in param_groups.items():
        ep_accuracy[ep].extend(accs)
    avg_ep_acc = {ep: np.mean(accs) for ep, accs in ep_accuracy.items()}
    plt.figure(figsize=(10, 6))
    plt.plot(list(avg_ep_acc.keys()), list(avg_ep_acc.values()), marker='o')
    plt.xlabel('Epochs')
    plt.ylabel('Average Accuracy')
    plt.title(f'{title_prefix} - Accuracy vs Epochs')
    plt.grid(True)
    plt.savefig(f'{output_prefix}_accuracy_vs_epochs.png')
    plt.close()

    # Plot 3: Accuracy vs Batch Size
    bs_accuracy = defaultdict(list)
    for (lr, ep, bs), accs in param_groups.items():
        bs_accuracy[bs].extend(accs)
    avg_bs_acc = {bs: np.mean(accs) for bs, accs in bs_accuracy.items()}
    plt.figure(figsize=(10, 6))
    plt.plot(list(avg_bs_acc.keys()), list(avg_bs_acc.values()), marker='o')
    plt.xlabel('Batch Size')
    plt.ylabel('Average Accuracy')
    plt.title(f'{title_prefix} - Accuracy vs Batch Size')
    plt.grid(True)
    plt.savefig(f'{output_prefix}_accuracy_vs_batch_size.png')
    plt.close()

    # Plot 4: Box plot for all accuracies
    all_accs = [result['metrics']['accuracy'] for result in results]
    plt.figure(figsize=(10, 6))
    plt.boxplot(all_accs)
    plt.ylabel('Accuracy')
    plt.title(f'{title_prefix} - Accuracy Distribution')
    plt.savefig(f'{output_prefix}_accuracy_boxplot.png')
    plt.close()

if __name__ == "__main__":
    # Load results
    automated_results = load_results('automated_experiments_results_20260507_045351.json')
    binary_results = load_results('binary_experiments_results_20260507_052608.json')

    # Generate graphs
    generate_graphs(automated_results, '10-Class Classification', 'automated')
    generate_graphs(binary_results, 'Binary Classification', 'binary')

    print("Graphs generated successfully!")