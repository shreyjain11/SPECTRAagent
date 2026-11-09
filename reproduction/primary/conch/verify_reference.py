"""Compare rebuilt public reference inputs against every retained original row."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'originals/scripts'))
import freeze_axes as axes
import analyze_spc as analysis


def verify(reference_path=None):
    ref = pd.read_csv(reference_path or ROOT / 'data/nct_reference_features.reconstructed.csv')
    discovery = pd.read_csv(ROOT / 'data/discovery.csv')
    columns = axes.feature_columns(ref)
    color = [c for c in columns if c.startswith(('r_', 'g_', 'b_', 'h_', 's_', 'v_', 'gray_hist_', 'gray_mean', 'gray_std'))]
    results = {'reference_rows': len(ref), 'feature_columns': columns, 'axes': {}, 'baselines': {}}
    new_axes = {}
    for key, selected in [('color_texture', columns), ('color', color)]:
        train, test, _, _ = axes.zscore(ref[selected].to_numpy(np.float32), discovery[selected].to_numpy(np.float32))
        new_axes[key] = -axes.mean_knn_distance(test, train, k=20)
    medians = {}
    for key, selected in [('tissue_fraction', ['tissue_fraction','white_fraction','dark_fraction','saturation_high_fraction']),
                          ('texture_complexity', ['gray_entropy','edge_mean','edge_std','gray_std'])]:
        median = ref[selected].median()
        medians[key] = median.to_dict()
        new_axes[key] = -np.sqrt(((discovery[selected]-median)**2).sum(axis=1)).to_numpy()
    results['medians'] = medians
    for key, values in new_axes.items():
        old = discovery[f'axis_nct_{key}_similarity'].to_numpy()
        levels, _ = axes.assign_similarity_levels(pd.Series(values),6)
        results['axes'][key] = {'rows': len(values), 'maximum_absolute_distance_error': float(np.max(abs(values-old))),
                                'mean_absolute_distance_error': float(np.mean(abs(values-old))),
                                'level_mismatches': int(np.sum(levels.to_numpy()!=discovery[f'level_nct_{key}_proximity'].to_numpy()))}
    scaler = StandardScaler()
    train = scaler.fit_transform(ref[columns].to_numpy(np.float32))
    labels = ref.label.to_numpy()
    logistic = LogisticRegression(max_iter=1000, C=1.0, solver='lbfgs', random_state=0)
    logistic.fit(train, labels)
    for phase in ['discovery', 'confirmation', 'expansion']:
        frame = pd.read_csv(ROOT / f'data/{phase}.csv')
        test = scaler.transform(frame[columns].to_numpy(np.float32))
        centroid = analysis.nearest_centroid_predict(train, labels, test)
        logreg = logistic.predict(test)
        results['baselines'][phase] = {'rows': len(frame),
                                      'centroid_prediction_mismatches': int(np.sum(centroid!=frame.baseline_centroid_pred)),
                                      'logistic_prediction_mismatches': int(np.sum(logreg!=frame.baseline_logistic_pred))}
    return results


if __name__ == '__main__':
    result = verify()
    print(json.dumps(result,indent=2))
