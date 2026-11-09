"""Current Transformers API exposed through the original evaluator interface.

Only model loading/output metadata are adapted. Original cohort order, seeds,
loops, diffusion settings, sample selection, CA extraction and metrics stay in
the original scientific evaluators. No PDB serialization/rounding is involved.
"""
import torch
from transformers import EsmFold2Model
from transformers.models.esmfold2.protein_utils import prepare_protein_features


class ESMFold2Model(EsmFold2Model):
    """Legacy class spelling, backed by the pinned current public implementation."""

    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        kwargs['output_loading_info'] = True
        model, info = super().from_pretrained(*args, **kwargs)
        problems = {key:info.get(key) for key in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs','conversion_errors','skipped_pp_keys') if info.get(key)}
        if problems:
            raise RuntimeError('Converted original checkpoint did not load completely: '+str(problems))
        model._spectra_loading_info = info
        return model

    @torch.no_grad()
    def infer_protein(self, sequence, **forward_kwargs):
        features = prepare_protein_features(sequence, device=self.device)
        output = self.fold(**features, **forward_kwargs)
        legacy_output = dict(output)
        for key in ('atom_to_token', 'ref_atom_name_chars', 'atom_attention_mask'):
            legacy_output[key] = features[key]
        legacy_output['token_attention_mask'] = features['attention_mask']
        return legacy_output
