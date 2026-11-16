import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm, spearmanr
import statsmodels.formula.api as smf
CTXS = ['rpe1', 'jurkat', 'hepg2']
rng = np.random.default_rng(20260722)

def boot_ci(x, n=10000, fn=np.mean):
    bs = np.empty(n)
    for b in range(n):
        bs[b] = fn(rng.choice(x, size=len(x), replace=True))
    return (float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))

def joint_gene_bootstrap(per, n_boot=10000, seed=20261115):
    """Resample genes jointly across the observed contexts; recompute tied ranks."""
    from scipy.stats import rankdata
    genes = sorted(set().union(*(set(d.gene) for d in per.values())))
    gene_index = {g: i for i, g in enumerate(genes)}
    blocks = {}
    fixed_weights = []
    for context in CTXS:
        d = per[context]
        if d.gene.duplicated().any():
            raise ValueError('Expected one perturbation unit per gene/context')
        ids = d.gene.map(gene_index).to_numpy()
        seen = d.seen_pair.to_numpy() == 1
        y = d.pearson_delta_state.to_numpy(dtype=float)
        norm_values = d.emb_norm.to_numpy(dtype=float)
        valid = (~seen) & np.isfinite(norm_values) & np.isfinite(y)
        if not np.isfinite(y).all():
            raise ValueError('Nonfinite prediction score')
        blocks[context] = (ids, seen, y, norm_values, valid)
        fixed_weights.append(int(valid.sum()) - 3)
    fixed_weights = np.asarray(fixed_weights, dtype=float)
    if (fixed_weights <= 0).any():
        raise ValueError('Insufficient unseen units for the fixed pooling weights')
    generator = np.random.default_rng(seed)
    draws = np.empty((n_boot, 2))
    for b in range(n_boot):
        multiplicity = np.bincount(generator.integers(0, len(genes), len(genes)), minlength=len(genes))
        context_deltas, context_rhos = [], []
        for context in CTXS:
            ids, seen, y, norm_values, valid = blocks[context]
            weights = multiplicity[ids]
            if weights[seen].sum() == 0 or weights[~seen].sum() == 0:
                raise ValueError('Degenerate seen/unseen bootstrap group')
            context_deltas.append(np.average(y[seen], weights=weights[seen]) - np.average(y[~seen], weights=weights[~seen]))
            # Expanding each gene by its sampled multiplicity preserves all tied ranks.
            x = np.repeat(norm_values[valid], weights[valid])
            yy = np.repeat(y[valid], weights[valid])
            rx, ry = rankdata(x), rankdata(yy)
            rho = np.corrcoef(rx, ry)[0, 1]
            if not np.isfinite(rho):
                raise ValueError('Degenerate context correlation in bootstrap; no zero substitution')
            context_rhos.append(rho)
        fisher = np.arctanh(np.clip(context_rhos, -0.999, 0.999))
        draws[b] = [np.mean(context_deltas), np.tanh(np.average(fisher, weights=fixed_weights))]
    table = pd.DataFrame(draws, columns=['binary_equal_context_delta', 'embedding_fisher_weighted_rho'])
    table.to_csv(WORK / 'results/pooled_gene_bootstrap_draws.csv', index=False)
    return {
        'resampling_unit': 'gene identity, shared across all observed contexts',
        'gene_clusters': len(genes), 'draws': n_boot, 'seed': seed,
        'scope': 'conditional on the three observed contexts; not independent-site replication',
        'embedding_context_weights': dict(zip(CTXS, fixed_weights.astype(int).tolist())),
        'binary_ci95': np.quantile(draws[:, 0], [0.025, 0.975]).tolist(),
        'embedding_ci95': np.quantile(draws[:, 1], [0.025, 0.975]).tolist(),
    }

def analyze_confirmation():
    per = {}
    for c in CTXS:
        df = pd.read_csv(str(WORK / f'results/per_unit_scores_{c}.csv'))
        nm = pd.read_csv(str(WORK / f'results/proximity_embedding_norms_{c}.csv'))[['gene', 'emb_norm']]
        df = df.merge(nm, on='gene', how='left', validate='one_to_one')
        per[c] = df
    out = {'contexts': {}}
    zs, ws, deltas = ([], [], [])
    for c in CTXS:
        df = per[c]
        s = df[df.seen_pair == 1]
        u = df[df.seen_pair == 0]
        d_state = s.pearson_delta_state.mean() - u.pearson_delta_state.mean()
        d_B1 = s.pearson_delta_B1.mean() - u.pearson_delta_B1.mean()
        d_B2 = s.pearson_delta_B2.mean() - u.pearson_delta_B2.mean()
        v = s.pearson_delta_state.var() / len(s) + u.pearson_delta_state.var() / len(u)
        z = d_state / np.sqrt(v)
        bs = np.empty(5000)
        sv, uv = (s.pearson_delta_state.values, u.pearson_delta_state.values)
        for b in range(5000):
            bs[b] = rng.choice(sv, len(sv), True).mean() - rng.choice(uv, len(uv), True).mean()
        ci = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        d = df.copy()
        d['log_effect'] = np.log(d.effect_mag)
        d['log_n'] = np.log(d.n_cells)
        m = smf.ols('pearson_delta_state ~ seen_pair + log_effect + log_n', data=d).fit()
        adj = dict(coef=float(m.params['seen_pair']), p=float(m.pvalues['seen_pair']))
        un = df[df.seen_pair == 0].dropna(subset=['emb_norm'])
        rho, p_two = spearmanr(un.emb_norm, un.pearson_delta_state)
        p_one = p_two / 2 if rho > 0 else 1 - p_two / 2
        un2 = un.copy()
        un2['log_effect'] = np.log(un2.effect_mag)
        un2['log_n'] = np.log(un2.n_cells)
        m2 = smf.ols('pearson_delta_state ~ emb_norm + log_effect + log_n', data=un2).fit()
        a1c_adj = dict(coef=float(m2.params['emb_norm']), p=float(m2.pvalues['emb_norm']))
        out['contexts'][c] = dict(n_seen=int(len(s)), n_unseen=int(len(u)), mean_pd_seen=float(s.pearson_delta_state.mean()), mean_pd_unseen=float(u.pearson_delta_state.mean()), delta_state=float(d_state), delta_boot_ci95=ci, z=float(z), delta_B1=float(d_B1), delta_B2=float(d_B2), adjusted_seen_coef=adj, a1c_spearman_rho=float(rho), a1c_p_one_sided=float(p_one), a1c_adjusted=a1c_adj, a1c_n_unseen=int(len(un)))
        zs.append(z)
        ws.append(np.sqrt(len(s) + len(u)))
        deltas.append(d_state)
    pooled_delta = float(np.mean(deltas))
    n_consistent = int(sum(d > 0 for d in deltas))
    fisher = np.array([np.arctanh(np.clip(out['contexts'][c]['a1c_spearman_rho'], -0.999, 0.999)) for c in CTXS])
    fixed_weights = np.array([out['contexts'][c]['a1c_n_unseen'] - 3 for c in CTXS])
    r_pool = float(np.tanh(np.average(fisher, weights=fixed_weights)))
    bootstrap = joint_gene_bootstrap(per)
    out['pooled'] = {
        'A1b_pooled_delta': pooled_delta,
        'A1b_gene_bootstrap_ci95': bootstrap['binary_ci95'],
        'A1b_contexts_consistent': n_consistent,
        'A1c_pooled_spearman': r_pool,
        'A1c_gene_bootstrap_ci95': bootstrap['embedding_ci95'],
        'uncertainty': bootstrap,
        'pooled_p_value': None,
        'correction': 'Joint gene-bootstrap intervals replace the independence-based binary Z/p and the invalid unnormalized embedding Z/p.',
    }
    with open(WORK / 'results/confirm_summary.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    rows = []
    for c in CTXS:
        df = per[c]
        for lev in ['seen_pair', 'unseen_E3', 'unseen_E2', 'unseen_E1']:
            sub = df[df.level == lev]
            rows.append(dict(context=c, level=lev, n=len(sub), pd_state=sub.pearson_delta_state.mean(), pd_B1=sub.pearson_delta_B1.mean(), pd_B2=sub.pearson_delta_B2.mean(), mse_state=sub.mse_delta_state.mean(), effect_mag=sub.effect_mag.mean()))
    spc = pd.DataFrame(rows)
    spc.to_csv(WORK / 'results/spc_table_confirm.csv', index=False)
    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
    order = ['seen_pair', 'unseen_E3', 'unseen_E2', 'unseen_E1']
    for ax, c in zip(axes, CTXS + ['k562']):
        if c == 'k562':
            df = pd.read_csv(WORK / 'results/per_unit_scores.csv')
            df['level'] = df.level.map(lambda l: 'seen_pair' if l == 'L4_seen_pair' else l.replace('L3_', '').replace('L2_', '').replace('L1_', ''))
        else:
            df = per[c]
        for col, lab, mk in [('pearson_delta_state', 'STATE', 'o-'), ('pearson_delta_B1', 'B1', 's--'), ('pearson_delta_B2', 'B2', '^--')]:
            ys = [df.loc[df.level == l, col].mean() for l in order]
            ax.plot(range(4), ys, mk, label=lab, ms=4)
        ax.set_xticks(range(4), ['seen', 'E3', 'E2', 'E1'], fontsize=8)
        ax.set_title(c)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel('pearson_delta')
    axes[-1].legend(loc='lower left', fontsize=8)
    fig.suptitle('SPC: pair-novelty axis (A1b) across contexts — confirmation')
    fig.tight_layout()
    fig.savefig(WORK / 'results/confirm_spc_plot.png', dpi=150)
analyze_confirmation()