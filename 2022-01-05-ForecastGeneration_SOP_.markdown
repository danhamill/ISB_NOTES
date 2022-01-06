#  Isabella Forecast Generation
  
  
The goal of this document is to describe how the Forecasts are generated for the WCM update HEC-WAT analysis. The structure of the "official" Isabella forecasts is shown below.
  
<center>
  
![](Figures/Forecast_Structure.png )
  
</center>
  
The forecast for a water year (<img src="https://latex.codecogs.com/gif.latex?wy"/>) is described as the summation of the remaining volume forecasts for the <img src="https://latex.codecogs.com/gif.latex?t"/> periods Feb-Jul (FJ), Mar-Jul (MJ), Apr-Jul (AJ), and May-Jul (MJ).
  
<p align="center"><img src="https://latex.codecogs.com/gif.latex?F_{wy,t}%20=%20F_{wy,FJ}%20+%20F_{wy,%20MJ}%20+%20F_{wy,%20AJ}%20+%20F_{wy,%20MJ}."/></p>  
  
  
We need to analyze the residuals (errors) between historical forecasts <img src="https://latex.codecogs.com/gif.latex?F_{wy,%20t}"/> and observed inflows <img src="https://latex.codecogs.com/gif.latex?Obs_{wy,t}"/>.  
  
<p align="center"><img src="https://latex.codecogs.com/gif.latex?E_{wy,%20t}%20=%20F_{wy,%20t}%20-%20Obs_{wy,t}"/></p>  
  
  
##  Data Transformation
  
  
 A historical analysis of the remaining-volume forecast errors (<img src="https://latex.codecogs.com/gif.latex?E_{wy,%20t}"/>) found the errors have a mild negative skew. The distributions of the z-scores of the untransformed (raw) remaining volume errors is shown below.
  
![](Figures/normalized_error_bar.png)
  
From a computation perspective, it is desirable to model the errors as normally distributed. The [Yeo-Johnson power transformation](https://en.wikipedia.org/wiki/Power_transform#Yeo%E2%80%93Johnson_transformation ) was evaluated to determine if the normal assumption could be used in this forecast generation model. An example probability plot of the untransformed (raw) and Yeo-Johnson transformed forecast errors for the Feb AJ remaining.  The Yeo-Johnson transformed values more closely follow the line of perfect agreement.
  
![](Figures/Feb_Yeo_probplot.png )
  
The remaining probability plots for Mar-July, Apr-July, May-July all show similar results where the Yeo-Johnson transformed values closely follow the line of perfect agreement.
  
The distribution of the Yeo-Johnson transformed z-values also appear normal.
  
![](Figures/data_transform_plots/normalized_yeoZ_density.png )
  
  
The statistical moments for the Yeo-Transformed data and non-transformed (row) errors show the skew of the transformed data are much closer to normal than the non-transformed (raw) errors.
  

  
```python
dataset     Yeo Johnson Errors           Errors (raw)
statistic   kurt  skew  variance  mean   kurt  skew   variance  mean
  
Feb         0.08   0.09  4.8e+10 -14345  0.007 -1.01  8.2e+10 -120989
Mar         0.28   0.06  2.0e+10   6129  0.953 -1.18  3.1e+10  -59828
Apr         1.79   0.49  4.0e+09  -1092  1.265 -0.36  4.2e+09  -11840
May         1.02   0.07  3.2e+09 -19378  2.437  0.86  3.0e+09  -11536
Jun         0.40  -0.16  1.7e+09  -3966  0.784 -0.92  2.0e+09  -12245
Jul         0.91  -0.16  4.0e+08   -127  3.337 -1.87  7.6e+08   -8735
```

  
Based on this demonstration of the data transformed errors, we can assume the errors are normally transformed using the YJ Transform.
  
##  Forecast Generation Procedure
  
  
1. Accept seed value from HEC-WAT
  
2. Generate 5 additional random numbers (<img src="https://latex.codecogs.com/gif.latex?r"/>) from the initial seed from HEC-WAT
    - <img src="https://latex.codecogs.com/gif.latex?r_{init}"/>
    - <img src="https://latex.codecogs.com/gif.latex?r_{Feb}"/>
    - <img src="https://latex.codecogs.com/gif.latex?r_{Mar}"/>
    - <img src="https://latex.codecogs.com/gif.latex?r_{Apr}"/>
    - <img src="https://latex.codecogs.com/gif.latex?r_{May}"/>
  
3. Convert the random numbers to z-scores using the inverse normal approximation algorithm described below.
  

  
    ```python
    #Get z-score from random variable
    # Inverse Normal distribution approximation (Z-score from cumulative probability)
    # https://www.johndcook.com/blog/python_phi_inverse/
    # based on algorithm given in "Handbook of Mathematical Functions" by Abramowitz and Stegun
    c = [2.515517, 0.802853, 0.010328]
    d = [1.432788, 0.189269, 0.001308]
  
    #note: log is base e by default if no base is specified
    if random_val < 0.5:
        t = (-2 * log(random_val)) ** 0.5
        num = (c[2] * t + c[1]) * t + c[0]
        den = ((d[2] * t + d[1]) * t + d[0]) * t + 1.0
        z = - (t - (num/den))
    else:
        t = (-2 * log(1.0 - random_val)) ** 0.5
        num = (c[2] * t + c[1]) * t + c[0]
        den = ((d[2] * t + d[1]) * t + d[0]) * t + 1.0
        z = (t - (num/den))
    ```

  
    We now have a sequence of uncorrelated z-scores described by:
    
    ```python
    z_scores = [z_init, z_feb, z_mar, z_apr, z_may]
    
    ```
  
  
4. To calculate a lag-1 autocorrelated sequence of forecasts, the sequence of z-scores can be calculated using a [moving average time series model](https://otexts.com/fpp2/MA.html ):
  
    ```python
    auto_corr_z_scores = [0,0,0,0]
    for i in len(z_scores[1:]):
        if i == 0:
            val = r * z_scores[0] + sqrt(1-r**2) * z_score[i]
            auto_corr_z_scores[i] = val
        else:
            val = r * z_score[i-1] + sqrt(1-r**2) * z_score[i]
            auto_corr_z_scores[i] = val
    ```
    
    The term <img src="https://latex.codecogs.com/gif.latex?r"/> in the lag1 autocorrelation sequence is estimated using the historical set of forecast errors (1976-2020). The autocorrelation between successive forecasts within a water year represents a linear relationship between lagged observations. By definition a value <img src="https://latex.codecogs.com/gif.latex?r_1"/> is between -1 and 1.  A value close to 1 indicates successive error terms will have the same sign, whereas a value close to negative 1 indicates successive error terms will alternate in sign. <img src="https://latex.codecogs.com/gif.latex?&#x5C;hat{r_1}"/> describes the set of lag1 auto correlation numbers for each forecast year between 1976 and 2020.
    
    <p align="center"><img src="https://latex.codecogs.com/gif.latex?&#x5C;hat{r_1}%20=%20Corr(Z_{wy,t},%20Z_{wy,t-1})"/></p>  
    
    
    Finally <img src="https://latex.codecogs.com/gif.latex?r_1"/> is calculated as the average of <img src="https://latex.codecogs.com/gif.latex?&#x5C;hat{r_1}"/>
    
    <p align="center"><img src="https://latex.codecogs.com/gif.latex?r_1%20=%20&#x5C;frac{&#x5C;sum%20{&#x5C;hat{r_1}}}{length(&#x5C;hat{ri_1})}"/></p>  
    
    
    For Isabella Lake, <img src="https://latex.codecogs.com/gif.latex?r_1%20=%200.316"/>
  
  
5. Reverse transform the z-scores using the fitted parameters for YJ Transformation, where <img src="https://latex.codecogs.com/gif.latex?y"/> is the autocorrelated z-score generated by step 4.
  
    The Yeo-Johnson transformation varies by <img src="https://latex.codecogs.com/gif.latex?&#x5C;lambda"/> and is described below:
    
    <center>
    
    ```python
    y = ((x + 1)**lmbda - 1) / lmbda,                for x >= 0, lmbda != 0
        -((-x + 1)**(2 - lmbda) - 1) / (2 - lmbda),  for x < 0, lmbda != 2
    ```
    

    
    The fitted <img src="https://latex.codecogs.com/gif.latex?&#x5C;lambda"/> values shown below.  
    
    <center>
    
    Month| Yeo Johnson <img src="https://latex.codecogs.com/gif.latex?&#x5C;lambda"/>  |
    -----|--------  |
    Feb  |  1.0495  |
    Mar  |  1.0511  |
    Apr  |  1.0223  |
    May  |  0.9808  |
    

  
6. Convert the reverse transformed z-scores to to errors using
  
<p align="center"><img src="https://latex.codecogs.com/gif.latex?E_{wy,%20t}%20=%20&#x5C;bar{E_t}%20+%20Z_{wy,t}%20*%20&#x5C;sigma_{E}"/></p>  
  
  
