Hola！从这一课开始，欢迎你进入神奇的并行计算编写过程

终于，从这一张过后又回到了中文PPT环境，终于不用翻一层再理解了（也许？）

注意，这一章节的PPT写的非常简单易懂，我也有很多地方是cv的，PPT制作水平还是太高了

## 向量化计算

首先，什么是向量化？

1. 我将用最直⽩、最不绕弯⼦的⽅式告诉你：向量化计算就是把一批数据当作一个整体同时运算，⽽不是一个一个依次处理。

2. 向量化的实践大于理论（会写就行了）

3. 向量化的熟练在于多练

4. 我们做向量化就是找出能向量化的地方然后向量化

![](../../images/2026-07-14-20-43-11.png)

这个时候我们就知道，原来我们前面讲了这么多硬件上的，指令上的，内核上的，储存上的并行，就是为了向量化做硬件支持

我们首先来看一段未经向量化的代码

```py
A = [[1,2,3],[4,5,6],[7,8,9]]
B = [[3,2,1],[6,5,4],[9,8,7]]

matrix_sum = [[0,0,0],[0,0,0],[0,0,0]]
fon i in range(3):
    fon j in range(3):
        matrix_sum[i][j]= A[i][j] + B[i][j]
```

第⼀个显著特点是⼤量使⽤ (嵌套) for 循环

本质上是，如果未经优化，⼀次就只执⾏⼀条，造成了极⼤的浪费

对于 3 * 3的矩阵相加来说，答案的每个位置只和原来的两个矩阵相应坐标的值有关，和其他位置都⽆关

也就是说，⼀个位置的运算，和其他位置都没有关系（⽆依赖关系）所以如果我有九个加法单元，那么⼀个单元处理⼀个位置就可以⾼效并⾏完成。

## 实战（没错你向量化就是这么务实）

```py

def function_2(seq: np.ndarray, sub: np.ndarray) -> np.ndarray:
    target = np.dot(sub, sub)
    candidates = np.where(np.correlate(seq, sub, mode='valid') == target
)[0]

check = candidates[:, np.newaxis] + np.arange(len(sub))
mask = np.all(np.take(seq, check) == sub, axis=-1)

return candidates [mask]

```

这段代码实现了一个查找对应数组段的功能，返回全数组中和我们朝朝数组相同的字段，然后返回他的起始位置值

我们想这段代码中有哪些地方是可以实现向量化的

首先，向量化的目标就是为了可以并行，我们现在算法的复杂度是len(seq) * len(sub)($On^2$)

一种可行的方法是把我们的查找组构建成向量，让这个向量和每一位做点积，和为平方的进入候选

然后从候选中选出完全相等的数组（我们可以写 == 但是在算法实现上这个语法的实现方法还是便历）

通过这样的操作，我们的最大复杂度就变成了len(seq) * len(sub) 最小是 len(seq)

其中矩阵乘法就可以通过向量化变成常数维复杂度的计算

```py
def function_1(seq: list[int], sub: list[int]) -> list[int]:
    return [
        i
        for i in range(len(seq) - len(sub) + 1)
        if seq[i:i + len(sub)] == sub
    ]
```
上面也体现出向量化的一种很重要的思想——用空间换时间

如果觉得这种优化微乎其微，不如来看看下面这些问题

![](../../images/2026-07-15-02-33-05.png)

![](../../images/2026-07-15-02-34-37.png)

![](../../images/2026-07-15-02-34-57.png)

## SIMD向量化

之前我们在讲解指令集优化的时候讲过SIMD，这个地方不赘述概念，而是讲一些新的东西

首先我们要澄清一个误区，SIMD的指令个数不等于加速倍数

真实的情况中还需要考虑我们内存带宽的使用，解码消耗的减少，背书只能是一种估计的方法

同时，⼀条AVX2指令能处理256位的数据，⼀条AVX512指令⼀次能处理512位数据，那为什么不再⻓亿点？

![](../../images/2026-07-15-02-38-54.png)

指令的功能是需要硬件实现的，⼀条指令处理8个double就意味⾄少需要8个double的运算单元，这意味着更⼤的⾯积，更⾼的成本，更多的发热

AVX512之前被戏称为⼤⽕炉，对CPU负载⾼频率跑⾼容易不稳定

而且这种高负载的硬件架构发热严重，过热导致降频，导致了AVX512表现不如AVX2的奇景

![](../../images/2026-07-15-02-40-06.png)

Intel的ISMD发展


![](../../images/2026-07-15-02-40-45.png)

ARM的ISMD发展

## SVE

AVX 是固定宽度向量：明确知道⼀次算 8 个、16 个。

SVE 是可伸缩向量：⼀次算⼏个由硬件决定，代码按“还能处理多少就处理多少”来写（SVL）。

```c
for (int i = 0; i < n; i += svcntw()) {
    svbool_t pg = svwhilelt_b32(i, n);
    svfloat32_t a = svld1(pg, A + i);
    svfloat32_t b = svld1(pg, B + i);
    svfloat32_t c = svadd_f32_x(pg, a, b);
    svst1(pg, C + i, c);
}
```

`svcntw()` = 当前机器⼀个 SVE 向量能放多少个 32-bit 元素

## 实战

首先，我们要从哪里获得我们的素材

https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html

这是一篇intel给出的官方加速文档

在阅读文档的时候，我们要注意几个东西

1. 善于搜索

![](../../images/2026-07-15-02-42-46.png)

2. 具体实现

![](../../images/2026-07-15-02-43-50.png)

下面给出我们的代码实战

使⽤ AVX512 对以下代码进⾏优化。

输⼊：

q: [D]

K: [T, D]

V: [T, D]

计算：

score[t] = q · K[t] / sqrt(D)

prob[t] = softmax(score)[t]

out[j] = Σ_t prob[t] * V[t][j]

首先给出我们的源码

```cpp
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <random>
#include <vector>
#include <immintrin.h>

#if defined(__GNUC__) && !defined(__clang__)
#define NO_VECTORIZE __attribute__((noinline, optimize("no-tree-vectorize")))
#else
#define NO_VECTORIZE __attribute__((noinline))
#endif

static double now_ms() {
    using namespace std::chrono;
    return std::chrono::duration<double, std::milli>(
        std::chrono::high_resolution_clock::now().time_since_epoch()).count();
}

NO_VECTORIZE
void attention_scalar_single_query(const float* q, const float* K, const float* V,
                                   float* out, int T, int D) {
    std::vector<float> scores(T);
    // 1
    const float scale = 1.0f / std::sqrt(static_cast<float>(D));
    
    // q:[D]
    // k:[T, D]
    for (int t = 0; t < T; ++t) {
        const float* k = K + static_cast<size_t>(t) * D;
        float acc = 0.0f;
        for (int j = 0; j < D; ++j) {
            float tmp = q[j] * k[j];  // vectorization 
            acc += tmp;  // vectorization
            // 规约的开销很大
        }
        scores[t] = acc * scale;
    }


    //2
    float max_score = -std::numeric_limits<float>::infinity();
    for (int t = 0; t < T; ++t) max_score = std::max(max_score, scores[t]); // vectorization

    float sum_exp = 0.0f;
    for (int t = 0; t < T; ++t) {
        float tmp = std::exp(scores[t] - max_score);  // vectorization
        sum_exp = sum_exp + tmp;  // vectorization
    }
    const float inv_sum = 1.0f / sum_exp;
    for (int t = 0; t < T; ++t) scores[t] *= inv_sum; // vectorization

    // 3
    for (int j = 0; j < D; ++j) out[j] = 0.0f;
    for (int t = 0; t < T; ++t) {
        const float* v = V + static_cast<size_t>(t) * D;
        const float p = scores[t];
        for (int j = 0; j < D; ++j) {
            float tmp = p * v[j]; // vectorization
            out[j] += tmp; // vectorization
        }
    }
}

static inline __mmask16 tail_mask16(int n) {
    return n >= 16 ? 0xFFFFu : static_cast<__mmask16>((1u << n) - 1u);
}

void attention_avx512_single_query(const float* q, const float* K, const float* V,
                                   float* out, int T, int D) {
    std::vector<float> scores(T);
    const float scale = 1.0f / std::sqrt(static_cast<float>(D));
    const int D16 = D & ~15;
    const int dtail = D - D16;
    const __mmask16 dmask = tail_mask16(dtail);

    // 1) score[t] = dot(q, K[t]) / sqrt(D)
    // AVX 512
    // float
    // 512 / 32 = 16 
    // q[0..15] * K[t][0..15] + q[16..31] * K[t][16..31] + ...
    // i = j
    for (int t = 0; t < T; ++t) {
        const float* k = K + static_cast<size_t>(t) * D;
        __m512 acc_tmp = _mm512_setzero_ps();
        for (int j = 0; j < D16; j += 16) {
            const __m512 qv = _mm512_loadu_ps(q + j); // q[0..15]
            const __m512 kv = _mm512_loadu_ps(k + j);
            acc_tmp = _mm512_fmadd_ps(qv, kv, acc_tmp); // acc += qv * kv
            // __m512 mul = _mm512_mul_ps(qv, kv);
            // acc = _mm512_add_ps(acc, mul);
        }
        if (dtail) {
            const __m512 qv = _mm512_maskz_loadu_ps(dmask, q + D16);
            const __m512 kv = _mm512_maskz_loadu_ps(dmask, k + D16);
            acc_tmp = _mm512_fmadd_ps(qv, kv, acc_tmp);
        }
        scores[t] = _mm512_reduce_add_ps(acc_tmp) * scale; // _mm512_reduce_add_ps(acc_tmp) = acc
    }

    // q:[D]
    // k:[T, D] -> kT: [D, T]
    // 对 T 维进行向量化
    // another way to compute scores using a TRANSPOSED K matrix

    std::vector<float> KT(static_cast<size_t>(D) * T);


    for (int tok = 0; tok < T; ++tok) {
        for (int jj = 0; jj < D; ++jj) {
            KT[static_cast<size_t>(jj) * T + tok] =
                K[static_cast<size_t>(tok) * D + jj];
        }
    }

    // kT: [D, T]
    // q: [D]

    const int T16 = T & ~15;

    int tok = 0;
    for (; tok < T16; tok += 16) {
        __m512 acc = _mm512_setzero_ps(); // store acc: store[0..15],[16..31],...

        for (int jj = 0; jj < D; ++jj) {
            const __m512 qv = _mm512_set1_ps(q[jj]); // q[16] = [q[jj], q[jj], ..., q[jj]]
            const __m512 kv = _mm512_loadu_ps(
                KT.data() + static_cast<size_t>(jj) * T + tok
            );
            acc = _mm512_fmadd_ps(qv, kv, acc); 
        }

        acc = _mm512_mul_ps(acc, _mm512_set1_ps(scale));
        _mm512_storeu_ps(scores.data() + tok, acc);
    }

    if (tok < T) {
        const __mmask16 m = tail_mask16(T - tok);

        __m512 acc = _mm512_setzero_ps();

        for (int jj = 0; jj < D; ++jj) {
            const __m512 qv = _mm512_set1_ps(q[jj]);
            const __m512 kv = _mm512_maskz_loadu_ps(
                m,
                KT.data() + static_cast<size_t>(jj) * T + tok
            );
            acc = _mm512_fmadd_ps(qv, kv, acc);
        }

        acc = _mm512_mul_ps(acc, _mm512_set1_ps(scale));
        _mm512_mask_storeu_ps(scores.data() + tok, m, acc);
    }

    // 2) softmax. max/sum can be vectorized; exp is deliberately scalar here
    // because standard AVX-512 intrinsics do not include a portable _mm512_exp_ps.
    const __m512 neg_inf = _mm512_set1_ps(-std::numeric_limits<float>::infinity()); // [inf, ..., inf]
    __m512 vmax = neg_inf;
    int t = 0;
    // [0, 16), [16, 32), ..., [T16, T) --> max
    // v1 = [0..15]
    // v2 = [16..31]
    // v3 = [32..47]
    // max_tmp = max(v1, v2)
    // max_tmp = max(max_tmp, v3)
    for (; t + 16 <= T; t += 16) {
        const __m512 s = _mm512_loadu_ps(scores.data() + t);
        vmax = _mm512_max_ps(vmax, s);
    }
    if (t < T) {
        const __mmask16 m = tail_mask16(T - t);
        const __m512 s = _mm512_mask_loadu_ps(neg_inf, m, scores.data() + t);
        vmax = _mm512_max_ps(vmax, s);
    }
    const float max_score = _mm512_reduce_max_ps(vmax); // max_tmp

    float sum_exp = 0.0f;
    for (int i = 0; i < T; ++i) {
        scores[i] = std::exp(scores[i] - max_score);
        sum_exp += scores[i];
    }
    const float inv_sum = 1.0f / sum_exp;
    for (int i = 0; i < T; ++i) scores[i] *= inv_sum;

    // 2) softmax with AVX-512 approximate exp.
    // 在 x=0 处泰勒展开

    // scores[i] = exp(scores[i] - max_score) / sum(exp(scores[i] - max_score))

    auto exp512_approx_ps = [](__m512 x) -> __m512 {
        // Clamp range to avoid overflow / underflow when constructing 2^n.
        const __m512 max_x = _mm512_set1_ps(88.3762626647949f);
        const __m512 min_x = _mm512_set1_ps(-87.3365447505531f);

        x = _mm512_min_ps(x, max_x);
        x = _mm512_max_ps(x, min_x);

        // exp(x) = 2^n * exp(r)
        // n = round(x / ln2)
        // r = x - n * ln2
        const __m512 log2e  = _mm512_set1_ps(1.44269504088896341f);
        const __m512 ln2_hi = _mm512_set1_ps(0.693359375f);
        const __m512 ln2_lo = _mm512_set1_ps(-2.12194440e-4f);

        const __m512 y = _mm512_mul_ps(x, log2e);

        const __m512i n = _mm512_cvt_roundps_epi32(
            y,
            _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC
        );

        const __m512 nf = _mm512_cvtepi32_ps(n);

        __m512 r = _mm512_fnmadd_ps(nf, ln2_hi, x);
        r = _mm512_fnmadd_ps(nf, ln2_lo, r);

        // exp(r) polynomial approximation.
        // 1 + r + r^2/2 + r^3/6 + r^4/24 + r^5/120 + r^6/720
        __m512 p = _mm512_set1_ps(1.0f / 720.0f);
        p = _mm512_fmadd_ps(p, r, _mm512_set1_ps(1.0f / 120.0f));
        p = _mm512_fmadd_ps(p, r, _mm512_set1_ps(1.0f / 24.0f));
        p = _mm512_fmadd_ps(p, r, _mm512_set1_ps(1.0f / 6.0f));
        p = _mm512_fmadd_ps(p, r, _mm512_set1_ps(1.0f / 2.0f));
        p = _mm512_fmadd_ps(p, r, _mm512_set1_ps(1.0f));
        p = _mm512_fmadd_ps(p, r, _mm512_set1_ps(1.0f));

        // Construct 2^n using float exponent bits.
        // float: exponent bias = 127, exponent field starts at bit 23.
        const __m512i pow2_bits = _mm512_slli_epi32(
            _mm512_add_epi32(n, _mm512_set1_epi32(127)),
            23
        );

        const __m512 pow2n = _mm512_castsi512_ps(pow2_bits);

        return _mm512_mul_ps(p, pow2n);
    };

    // 2.1) max_score = max(scores)
    const __m512 neg_inf = _mm512_set1_ps(-std::numeric_limits<float>::infinity());

    __m512 vmax = neg_inf;

    int t = 0;
    for (; t + 16 <= T; t += 16) {
        const __m512 s = _mm512_loadu_ps(scores.data() + t);
        vmax = _mm512_max_ps(vmax, s);
    }

    if (t < T) {
        const __mmask16 m = tail_mask16(T - t);
        const __m512 s = _mm512_mask_loadu_ps(neg_inf, m, scores.data() + t);
        vmax = _mm512_max_ps(vmax, s);
    }

    const float max_score = _mm512_reduce_max_ps(vmax);
    const __m512 v_max_score = _mm512_set1_ps(max_score);

    // 2.2) scores[i] = approx_exp(scores[i] - max_score)
    // Meanwhile accumulate sum_exp.
    __m512 vsum = _mm512_setzero_ps();

    t = 0;
    for (; t + 16 <= T; t += 16) {
        const __m512 s = _mm512_loadu_ps(scores.data() + t);
        const __m512 x = _mm512_sub_ps(s, v_max_score);
        const __m512 e = exp512_approx_ps(x);

        _mm512_storeu_ps(scores.data() + t, e);
        vsum = _mm512_add_ps(vsum, e);
    }

    if (t < T) {
        const __mmask16 m = tail_mask16(T - t);

        const __m512 s = _mm512_maskz_loadu_ps(m, scores.data() + t);
        const __m512 x = _mm512_sub_ps(s, v_max_score);
        __m512 e = exp512_approx_ps(x);

        // Invalid lanes must not contribute to sum_exp.
        e = _mm512_maskz_mov_ps(m, e);

        _mm512_mask_storeu_ps(scores.data() + t, m, e);
        vsum = _mm512_add_ps(vsum, e);
    }

    const float sum_exp = _mm512_reduce_add_ps(vsum);
    const __m512 inv_sum = _mm512_set1_ps(1.0f / sum_exp);

    // 2.3) scores[i] /= sum_exp
    t = 0;
    for (; t + 16 <= T; t += 16) {
        const __m512 e = _mm512_loadu_ps(scores.data() + t);
        const __m512 p = _mm512_mul_ps(e, inv_sum);
        _mm512_storeu_ps(scores.data() + t, p);
    }

    if (t < T) {
        const __mmask16 m = tail_mask16(T - t);
        const __m512 e = _mm512_maskz_loadu_ps(m, scores.data() + t);
        const __m512 p = _mm512_mul_ps(e, inv_sum);
        _mm512_mask_storeu_ps(scores.data() + t, m, p);
    }

    // 3) out = softmax(score) * V
    int j = 0;
    for (; j < D16; j += 16) _mm512_storeu_ps(out + j, _mm512_setzero_ps());
    if (dtail) _mm512_mask_storeu_ps(out + D16, dmask, _mm512_setzero_ps());

    for (int tok = 0; tok < T; ++tok) {
        const float* v = V + static_cast<size_t>(tok) * D;
        const __m512 p = _mm512_set1_ps(scores[tok]);
        for (j = 0; j < D16; j += 16) {
            __m512 ov = _mm512_loadu_ps(out + j);
            const __m512 vv = _mm512_loadu_ps(v + j);
            ov = _mm512_fmadd_ps(p, vv, ov);
            _mm512_storeu_ps(out + j, ov);
        }
        if (dtail) {
            __m512 ov = _mm512_maskz_loadu_ps(dmask, out + D16);
            const __m512 vv = _mm512_maskz_loadu_ps(dmask, v + D16);
            ov = _mm512_fmadd_ps(p, vv, ov);
            _mm512_mask_storeu_ps(out + D16, dmask, ov);
        }
    }
}

int main(int argc, char** argv) {
    const int T = (argc > 1) ? std::atoi(argv[1]) : 1025;
    const int D = (argc > 2) ? std::atoi(argv[2]) : 80;
    const int repeat = (argc > 3) ? std::atoi(argv[3]) : 50;

    std::vector<float> q(D), K(static_cast<size_t>(T) * D), V(static_cast<size_t>(T) * D);
    std::vector<float> out_s(D), out_v(D);

    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
    for (float& x : q) x = dist(rng);
    for (float& x : K) x = dist(rng);
    for (float& x : V) x = dist(rng);

    attention_scalar_single_query(q.data(), K.data(), V.data(), out_s.data(), T, D);
    attention_avx512_single_query(q.data(), K.data(), V.data(), out_v.data(), T, D);

    float max_err = 0.0f;
    for (int i = 0; i < D; ++i) max_err = std::max(max_err, std::abs(out_s[i] - out_v[i]));

    double t0 = now_ms();
    for (int r = 0; r < repeat; ++r)
        attention_scalar_single_query(q.data(), K.data(), V.data(), out_s.data(), T, D);
    double t1 = now_ms();
    for (int r = 0; r < repeat; ++r)
        attention_avx512_single_query(q.data(), K.data(), V.data(), out_v.data(), T, D);
    double t2 = now_ms();

    std::cout << "single-query attention: T=" << T << ", D=" << D << ", repeat=" << repeat << "\n";
    std::cout << "scalar avg: " << (t1 - t0) / repeat << " ms\n";
    std::cout << "avx512 avg: " << (t2 - t1) / repeat << " ms\n";
    std::cout << "max_err: " << max_err << "\n";
    std::cout << ((max_err < 1e-4f) ? "PASS\n" : "FAIL\n");
    return (max_err < 1e-4f) ? 0 : 1;
}

```

![](../../images/2026-07-15-02-44-50.png)

