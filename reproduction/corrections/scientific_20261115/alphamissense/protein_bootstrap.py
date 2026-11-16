"""Protein-cluster uncertainty while preserving each reported ratio estimand."""
import numpy as np
import pandas as pd

def protein_cluster_interval(data, value_column, weight_column=None, *, rng, replicates=5000):
    """Resample proteins; keep all repeated assays for each selected protein.

    The estimate remains sum(weight * value) / sum(weight), not the mean of
    protein means. With no weight column it remains the mean over assays.
    A single independent cluster cannot identify between-protein uncertainty.
    """
    if data.empty:
        return dict(ci_low=np.nan, ci_high=np.nan, bootstrap_proteins=0,
                    ci_status='no_eligible_proteins')
    if data.protein.isna().any():
        raise ValueError('Every assay must have a protein identifier.')
    values=data[value_column].to_numpy(float)
    weights=np.ones(len(data)) if weight_column is None else data[weight_column].to_numpy(float)
    if not (np.isfinite(values).all() and np.isfinite(weights).all() and (weights>0).all()):
        raise ValueError('Bootstrap values and positive weights must be finite.')
    totals=pd.DataFrame({'protein':data.protein.to_numpy(),
                         'numerator':weights*values,'denominator':weights}).groupby('protein',sort=True).sum()
    proteins=len(totals)
    if proteins<2:
        return dict(ci_low=np.nan,ci_high=np.nan,bootstrap_proteins=proteins,
                    ci_status='insufficient_independent_proteins')
    chosen=rng.integers(0,proteins,size=(replicates,proteins))
    numerator=totals.numerator.to_numpy();denominator=totals.denominator.to_numpy()
    draws=numerator[chosen].sum(axis=1)/denominator[chosen].sum(axis=1)
    if np.ptp(draws)<=np.finfo(float).eps*max(1.0,float(np.abs(draws).max())):
        return dict(ci_low=np.nan,ci_high=np.nan,bootstrap_proteins=proteins,
                    ci_status='no_empirical_resampling_variation')
    low,high=np.quantile(draws,[.025,.975])
    return dict(ci_low=float(low),ci_high=float(high),bootstrap_proteins=proteins,
                ci_status='estimated_from_protein_clusters')
