# 可分离变量

$\frac{dx}{\varPhi y}=f(x)dx \to{\int{\frac{dy}{\varPhi (y)}}} = \int{f(x)dx + c}(\varphi (y) \neq 0)$
如果$\exist y_0 S.T. \varphi(y)=0$那么$y=y_0$也是方程的解

# 齐次微分方程
$\frac{dy}{dx} = g(\frac{y}{x})$
换元 然后再对两边求导
$\frac{dy}{dx} = x\frac{du}{dx}+u \to \frac{du}{dx} = \frac{g(u)-u}{x}$
回到1中，回代换元
当然，遇到$\frac{dy}{dx} = f({a_1 x+b_1 y+c_1})$
也是直接换元然后求导

$\frac{dy}{dx} = f(\frac{a_1 x+b_1 y+c_1}{a_2 x+b_2 y+c_2})$