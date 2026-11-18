# HICE Research Methodology & Experimental Protocol

## 1. Experimental Configurations
To isolate and measure the contribution of each algorithmic stage, HICE benchmarks four distinct configurations on identical hardware:

1. **Baseline Standard:** AES-256-GCM only
2. **Configuration A:** Chaotic Map (Logistic) + AES-256-GCM
3. **Configuration B:** Cellular Automata (Rule 30/90) + AES-256-GCM
4. **Configuration C (HICE Full Hybrid):** Chaotic Map + Cellular Automata + AES-256-GCM

## 2. Statistical Metrics & Definitions

### Shannon Information Entropy
Measures the randomness of pixel intensities:
$$H(m) = -\sum_{i=0}^{255} P(m_i) \log_2 P(m_i)$$
Ideal theoretical value for an 8-bit channel is **8.0000**.

### Number of Pixels Change Rate (NPCR)
Measures the percentage of different pixels between two ciphertexts when one original pixel is flipped:
$$\text{NPCR} = \frac{\sum_{i,j} D(i,j)}{W \times H} \times 100\%$$
Where $D(i,j) = 1$ if $C_1(i,j) \neq C_2(i,j)$, else $0$. Ideal threshold: **> 99.6%**.

### Unified Average Changing Intensity (UACI)
Measures average intensity of differences:
$$\text{UACI} = \frac{1}{W \times H} \sum_{i,j} \frac{|C_1(i,j) - C_2(i,j)|}{255} \times 100\%$$
Ideal threshold: **~ 33.4%**.

### Adjacent Pixel Correlation
Evaluates spatial correlation between adjacent pixels along Horizontal, Vertical, and Diagonal axes:
$$r_{xy} = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}$$
Natural medical images exhibit correlation $r \approx 0.95 - 0.99$. Strong cryptosystems push $r \to 0.00$.

## 3. Methodological Integrity Notice
High entropy and zero correlation are necessary properties of good confusion and diffusion, but they do **not** constitute formal cryptographic proof of IND-CCA2 security. Formal security in HICE is established by AES-256-GCM.
