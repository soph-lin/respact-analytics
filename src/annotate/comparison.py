# Compare two annotations using Cohen's Kappa.

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import cohen_kappa_score
from pathlib import Path
import warnings

# Get the project root directory
project_root = Path(__file__).parent.parent.parent

# Load all annotation files
annotation_files = list((project_root / "annotations").glob("*.json"))
all_annotations = []
annotator_labels = []

# Group files by their dataset name (e.g., Respact-Opt_12, Respact-Opt-Friction-v73)
file_groups = {}
for file in annotation_files:
    # Extract dataset name and version
    parts = file.name.split('.')
    if len(parts) >= 3 and parts[-2] in ['v1', 'v2']:
        dataset_name = '.'.join(parts[:-2])
        version = parts[-2]
        if dataset_name not in file_groups:
            file_groups[dataset_name] = {}
        file_groups[dataset_name][version] = file

# Only keep datasets that have both v1 and v2 versions
valid_datasets = {name: files for name, files in file_groups.items() 
                 if 'v1' in files and 'v2' in files}

# Load files in order, separating v1 and v2
v1_annotations = []
v2_annotations = []
v1_labels = []
v2_labels = []

for dataset_name, files in valid_datasets.items():
    # Load v1
    df = pd.read_json(files['v1'])
    v1_annotations.append(df)
    v1_labels.append(f"{dataset_name}_v1")
    
    # Load v2
    df = pd.read_json(files['v2'])
    v2_annotations.append(df)
    v2_labels.append(f"{dataset_name}_v2")

# Combine all annotations for label extraction
all_annotations = v1_annotations + v2_annotations

# Get all unique labels
all_labels = set()
for df in all_annotations:
    for labels in df["labels"]:
        all_labels.update(labels.keys())
all_labels = sorted(list(all_labels))

# Convert to binary matrix for each label
def create_binary_matrix(df, labels):
    matrix = np.zeros((len(df), len(labels)))
    for i, row_labels in enumerate(df["labels"]):
        for j, label in enumerate(labels):
            if label in row_labels and row_labels[label] > 0:
                matrix[i, j] = 1
    return matrix

# Create binary matrices for v1 and v2 annotators
v1_matrices = [create_binary_matrix(df, all_labels) for df in v1_annotations]
v2_matrices = [create_binary_matrix(df, all_labels) for df in v2_annotations]

# Calculate kappa matrix for each label
n_v1 = len(v1_matrices)
n_v2 = len(v2_matrices)
kappa_matrices = []

def safe_kappa(y1, y2):
    """Calculate kappa with proper error handling"""
    # Check for degenerate cases
    y1_unique = np.unique(y1)
    y2_unique = np.unique(y2)
    
    # If both arrays are identical (all 0s or all 1s)
    if np.array_equal(y1, y2):
        return 1.0
    
    # If one array is all 0s and the other is all 1s (perfect disagreement)
    if (len(y1_unique) == 1 and len(y2_unique) == 1 and 
        y1_unique[0] != y2_unique[0]):
        print("Warning: Perfect disagreement detected - one annotator marked all as present while the other marked all as absent")
        return np.nan
    
    # If one array has no variation (all 0s or all 1s)
    if len(y1_unique) == 1 or len(y2_unique) == 1:
        print("Warning: One annotator used only one value (all 0s or all 1s)")
        return np.nan
    
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            kappa = cohen_kappa_score(y1, y2, labels=[0, 1])
            return kappa
    except Exception as e:
        print(f"Warning: Error calculating kappa: {str(e)}")
        return np.nan

for label_idx in range(len(all_labels)):
    kappa_matrix = np.zeros((n_v2, n_v1))  # Note: swapped dimensions
    for i in range(n_v1):
        for j in range(n_v2):
            # Only compare corresponding datasets
            if i == j:
                kappa = safe_kappa(
                    v1_matrices[i][:, label_idx],
                    v2_matrices[j][:, label_idx]
                )
                kappa_matrix[j, i] = kappa  # Note: swapped indices
            else:
                kappa_matrix[j, i] = np.nan  # Note: swapped indices
    kappa_matrices.append(kappa_matrix)

# Calculate average kappa matrix across all labels
avg_kappa_matrix = np.nanmean(kappa_matrices, axis=0)

# Create heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(avg_kappa_matrix, 
            annot=True, 
            fmt='.2f',
            cmap='RdYlBu_r',
            vmin=-1,
            vmax=1,
            square=True,
            mask=np.isnan(avg_kappa_matrix),
            xticklabels=v1_labels,
            yticklabels=v2_labels)
plt.title('Inter-Annotator Agreement Heatmap\n(Average Cohen\'s Kappa across all labels)', pad=20)
plt.xlabel('Annotator 1 (v1)', labelpad=10)
plt.ylabel('Annotator 2 (v2)', labelpad=10)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)

# Save plot
plt.tight_layout(pad=2.0)
plt.savefig(project_root / 'annotations' / 'agreement_heatmap.png', 
            bbox_inches='tight', 
            dpi=300,
            pad_inches=0.5)
plt.close()

# Create individual heatmaps for each label
n_cols = min(3, len(all_labels))  # Maximum 3 columns
n_rows = (len(all_labels) + n_cols - 1) // n_cols

# Create figure
fig = plt.figure(figsize=(11 * n_cols, 9 * n_rows))

# Create gridspec
gs = fig.add_gridspec(n_rows, n_cols + 1, 
                     width_ratios=[10] * n_cols + [0.5], 
                     hspace=1.2,
                     wspace=0.3)

# Create axes for each subplot
axes = []
for i in range(n_rows):
    for j in range(n_cols):
        if i * n_cols + j < len(all_labels):
            ax = fig.add_subplot(gs[i, j])
            axes.append(ax)

# Create the heatmaps without colorbars first
for idx, (label, kappa_matrix) in enumerate(zip(all_labels, kappa_matrices)):
    g = sns.heatmap(kappa_matrix,
                annot=True,
                fmt='.2f',
                cmap='RdYlBu_r',
                vmin=-1,
                vmax=1,
                square=True,
                ax=axes[idx],
                mask=np.isnan(kappa_matrix),
                xticklabels=v1_labels,
                yticklabels=v2_labels,
                cbar=False)
    
    axes[idx].set_title(f'Kappa Agreement: {label}', pad=20)
    axes[idx].set_xlabel('Annotator 1 (v1)', labelpad=10)
    axes[idx].set_ylabel('Annotator 2 (v2)', labelpad=10)
    # Adjust label positions and rotation
    axes[idx].set_xticklabels(axes[idx].get_xticklabels(), 
                             rotation=45, 
                             ha='right',
                             position=(0, -0.2))

# Create a single colorbar for all subplots
cbar_ax = fig.add_subplot(gs[:, -1])
norm = plt.Normalize(vmin=-1, vmax=1)
scalar_mappable = plt.cm.ScalarMappable(norm=norm, cmap='RdYlBu_r')
cbar = fig.colorbar(scalar_mappable, cax=cbar_ax)
cbar.set_label('Cohen\'s Kappa', labelpad=10)

# Save figure
plt.savefig(project_root / 'annotations' / 'agreement_heatmap_by_label.png',
            bbox_inches='tight',
            dpi=300,
            pad_inches=1.0)
plt.close()

# Print information about annotators
print("\nAnnotators included in analysis:")
print("Annotator 1 (v1):")
for i, label in enumerate(v1_labels):
    print(f"{i}: {label}")
print("\nAnnotator 2 (v2):")
for i, label in enumerate(v2_labels):
    print(f"{i}: {label}")

# Print detailed kappa information for each label
print("\nDetailed Kappa Analysis for each label:")
for label, kappa_matrix in zip(all_labels, kappa_matrices):
    print(f"\nLabel: {label}")
    for i in range(len(v1_labels)):
        kappa = kappa_matrix[i, i]
        if np.isnan(kappa):
            print(f"  {v1_labels[i]} vs {v2_labels[i]}: Invalid comparison (see warnings above)")
        else:
            print(f"  {v1_labels[i]} vs {v2_labels[i]}: {kappa:.3f}")

print(f"\nOverall Average Cohen's Kappa: {np.nanmean(avg_kappa_matrix):.3f}")

