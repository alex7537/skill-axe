# WAM concept ladder

Use the entry matching the immediate question. Each gives a precise intuition, a distinction, and a falsifiable check.

## Latent

A latent is a learned compressed tensor that preserves information useful to the decoder and generative model. It is not one scalar “meaning vector.” In WAM it retains channel, time, height, and width axes.

Distinguish raw RGB, VAE latent, patch token, and global transformer representation. Check by encoding and decoding one clip and printing every intermediate shape.

## Video VAE

The VAE is a pretrained video codec: encoder maps RGB clips to compact spatiotemporal latents; decoder reconstructs RGB. WAM trains dynamics in this cheaper latent space. The wrapper may use the posterior mean deterministically even though the architecture is variational.

Distinguish compression quality from future prediction quality. Evaluate VAE-only reconstruction before blaming the DiT for missing detail.

## Causal video encoding

Temporal causality means a prefix latent cannot depend on future RGB. Past-only padding and cached earlier chunks enforce this in causal convolutions. It does not mean the DiT generates one frame at a time; the DiT can denoise the future chunk jointly.

Check by encoding the same prefix alone and before two different futures; corresponding prefix latents should match within tolerance.

## Why 9 plus 16 frames

Concatenating known history and future target preserves one continuous video sequence and matches the pretrained VAE's temporal geometry. Separately encoding the prefix supplies condition; slicing/masking makes only future latent steps contribute to video loss.

Check that 9 frames map to 3 latent steps, 25 map to 7, and the first 3 are excluded from loss.

## MLP and activation

An MLP stacks learned affine maps and nonlinear activations. Without a nonlinearity, two linear layers collapse to one affine map. SiLU, `x * sigmoid(x)`, is a smooth input-dependent gate that keeps some negative activations and gradients.

The MLP maps each 82D state/action vector to DiT width; position embeddings plus the transformer model time. Inspect token shapes before and after the encoder.

## Self-attention and cross-attention

Self-attention lets video, state, and action tokens exchange information in the shared sequence. Cross-attention lets them query language/robot context. This coupling supports joint modeling, but attention weights alone do not prove causal control.

Check by shuffling one condition modality across the batch and measuring both outputs.

## Dual Flow Matching

The model observes corrupted video/action at sampled continuous time and predicts the vector field transporting noise toward data under the repository's sign convention. Loss on both heads trains a shared conditional vector field.

Lower vector-field MSE does not guarantee perceptual quality, action following, or stable rollout. Plot target/prediction norms by noise time and ablate each loss while monitoring the other modality.

## Closed-loop world model

Predicted future observations/actions influence later context. Small one-step errors can compound as the model consumes out-of-distribution states. Distinguish teacher-forced, one-step open-loop, and recursive rollout.

Check error versus rollout depth and separate state-replacement from video-generation errors.

## Causal claim about action

Training `p(video_future | history, action)` can learn correlations. To argue action controls future, intervene on action while holding history, language, noise seed, and other inputs fixed; require directionally correct visual changes.

Use counterfactual action pairs, negative controls, and repeated seeds. Do not call diversity or correlation “action correctness.”

## Evaluation layers

Evaluate separately: codec reconstruction, open-loop future prediction, action-conditioned controllability/action accuracy, and closed-loop task success/stability.

Freeze sample coverage, metric direction, normalization, weighting, missing-data policy, and critical gates. A composite score is meaningful only after every component is independently auditable.
