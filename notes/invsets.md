# Invsets

Given a set $U$, a permutation oracle $O \rightarrow \{0, 1\}$

An order is defined as a series of sets $S_1$, $S_2$, ..., $S_n$ where $|S_n| = n$ and $S_n \subseteq U$, i.e. $\emptyset \subset S_1 \subset S_2 \subset ... \subset S_n \subseteq U$.

The inversion set ($invset(\pi)$) of a permutation $\pi$ of $n$ elements is the set of pairs $(i, j)$ such that $i < j$ and $\pi(i) > \pi(j)$

For each pair $(i, j) | i \neq j$, initialize counters:
- $M^+_{(i, j)} \gets 0$ // positive (accepted) count
- $M^-_{(i, j)} \gets 0$ // negative (rejected) count

For each permutation $\pi$ queried:
- If $O(\pi) = 1$ (accepted): for each $(i, j) \in invset(\pi)$, increment $M^+_{(i, j)} \gets M^+_{(i, j)} + 1$
- If $O(\pi) = 0$ (rejected): for each $(i, j) \in invset(\pi)$, increment $M^-_{(i, j)} \gets M^-_{(i, j)} + 1$

$P_{observed}^+(i, j) = M^+_{(i, j)} / N^+$ (frequency in positive samples)

$P_{observed}^-(i, j) = M^-_{(i, j)} / N^-$ (frequency in negative samples)

$P_{observed+}(x) = (1-\epsilon)P(1) + \epsilon(1 - P(1))$
$P_{observed-}(x) = (1-\epsilon)P(0) + \epsilon(1 - P(0))$
$P(1) = 1 - P(0)$


Greatest Lower Bound

 $meet(A, B) \rightarrow invset(A) \cap invset(B)$

Greatest Upper Bound
 $join(A, B) \rightarrow invset(A) \cup invset(B)$

Assume oracle outputs are flipped with probability $\epsilon$. We can estimate the 'true' probability $P(x)$ from our observed samples $P_{obs}(x)$ as follows:

$P_{observed}(x) = (1 - \epsilon) * P(x) + \epsilon * (1 - P(x))$

$P_{observed}(x) = P(x) - \epsilon P(x)  + \epsilon - \epsilon P(x)$

$P_{observed}(x) = P(x) - \epsilon P(x) - \epsilon P(x) + \epsilon$

$P_{observed}(x) = P(x) (1 - \epsilon - \epsilon) + \epsilon$

$P_{observed}(x) = P(x) (1 - 2\epsilon) + \epsilon$

$P_{observed}(x) - \epsilon = P(x) (1 - 2\epsilon)$

$\frac{P_{observed}(x) - \epsilon}{1 - 2\epsilon} = P(x)$


$$ f = (1-p)q + p(1-q) $$
$$ f = q - pq + p - pq $$
$$ f = q - pq + p - pq $$
$$ f = q(1-p-p) + p $$
$$ f = q(1-2p) + p $$
$$ f - p = q (1 - 2p) $$
$$ \frac{f - p}{1 - 2p} = q $$
x = (1 - p) * x + p * (x)


$P(\text{observed} = 1 \mid \text{true} = 0) = p$
$P(\text{observed} = 1 \mid \text{true} = 1) = 1-p$
$P(\text{observed} = 0 \mid \text{true} = 0) = 1-p$
$P(\text{observed} = 0 \mid \text{true} = 1) = p$


if $O(A) = 1$ and $O(B) = 1$

 ?

if $O(A) = 0$ and $O(B) = 0$

 ?

if $O(A) = 1$ and $O(B) = 0$

 ?

if $O(A) = 0$ and $O(B) = 1$

 ?

# DB

Record:
- Key
- Version
- Payload