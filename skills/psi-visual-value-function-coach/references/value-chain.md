# PSI visual value chain

Use this reference when formulas, shapes, or a complete explanation are needed.

## Default visual path

```text
RGB or RGB+Mask [B, 3/4, 224, 224]
-> ViT-S/R26 tokens [B, 49, 384]
-> feature map [B, 384, 7, 7]
-> SpatialSoftmax coordinates [B, 384, 2]
-> flattened visual feature [B, 768]
-> MLP value head
```

SpatialSoftmax computes an expected 2-D location within each feature channel. It does not select a value atom and should not be conflated with the Softmax over value logits.

## Reward and MC target

Humans define task stages and a per-transition scoring rule. The discounted return-to-go is

\[
G_t = r_t + \gamma r_{t+1} + \gamma^2 r_{t+2} + \cdots.
\]

This is the MC supervision attached to the current observation. It means future cumulative task score under the recorded trajectory, not an intrinsic visual property.

Scalar value training uses

\[
L_{MSE}=(V_\theta(s_t)-G_t)^2.
\]

## Distributional value

Choose fixed numerical support points

\[
z_i=v_{min}+i\frac{v_{max}-v_{min}}{N-1}.
\]

The MLP outputs logits `l_i`; predicted probabilities are

\[
p_i=\operatorname{softmax}(l)_i.
\]

Project scalar `G` onto its adjacent support points. With continuous index

\[
b=(G-v_{min})/\Delta z,\quad l=\lfloor b\rfloor,\quad u=\lceil b\rceil,
\]

assign

\[
q_l=u-b,\qquad q_u=b-l.
\]

If `l == u`, put mass one on that atom. The intended invariants are

\[
\sum_i q_i=1,
\qquad
\sum_i q_i z_i=\operatorname{clip}(G,v_{min},v_{max}).
\]

Cross-entropy is

\[
L_{CE}=-\sum_i q_i\log p_i.
\]

Inference converts the distribution back to a scalar expectation:

\[
V(s)=\sum_i p_i z_i.
\]

The support points are value bins, not task-stage classes. The target distribution is derived from `G`; the prediction distribution is learned from images.

## IQL targets

The value target is built from conservative twin-Q estimates:

\[
Q_{min}=\min(Q_1(s,a),Q_2(s,a)),\qquad \delta=Q_{min}-V(s).
\]

Expectile regression weights positive and negative residuals asymmetrically:

\[
L_V=|\tau-\mathbf{1}(\delta<0)|\delta^2.
\]

The Q target is

\[
y=r+\gamma(1-d)V(s'),
\]

and each Q network uses MSE against `y`.

## Gradient interpretation

Loss backpropagates through all operations that produced the prediction. Every participating parameter with `requires_grad=True` can update. A frozen visual encoder supplies a fixed representation, so only downstream heads learn. Softmax learning is not a hard selection of the largest atom: changing one logit changes the normalized probabilities of all atoms.

## Small falsification checks

- Assert projected target mass equals one for exact atoms, between-atom targets, and clipped boundaries.
- Assert projected support expectation reconstructs the clipped scalar.
- Overfit one small batch and confirm loss falls.
- Shuffle `return_to_go`; held-out performance should collapse if the model was learning the intended visual-value mapping.
- Compare RGB, zero-Mask, and shuffled-Mask predictions.
- Compare frozen and unfrozen visual encoders when stage information may be absent from pretrained features.
