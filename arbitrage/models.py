from django.db import models


class TradingViewData(models.Model):
    hash_pair = models.CharField(max_length=255, unique=True, primary_key=True)
    exchange = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    cur_1 = models.CharField(max_length=16)
    cur_2 = models.CharField(max_length=16)
    price_1 = models.FloatField()
    price_2 = models.FloatField()
    type = models.CharField(max_length=50)
    subtype = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now=True)
    reversed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Trading View Data'
        
    # def __str__(self):
    #     return f'{self.name} {self.exchange} {round(self.price_1, 3)}'
    
    
class CrossExchangeArbitrage(models.Model):
    hash_pair = models.CharField(max_length=255, unique=True, primary_key=True)
    hash_pair_1 = models.ForeignKey(
        TradingViewData,
        related_name='hash_pair_1',
        on_delete=models.CASCADE
    )
    hash_pair_2 = models.ForeignKey(
        TradingViewData,
        related_name='hash_pair_2',
        on_delete=models.CASCADE
    )
    hash_pair_3 = models.ForeignKey(
        TradingViewData,
        related_name='hash_pair_3',
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    hash_pair_4 = models.ForeignKey(
        TradingViewData,
        related_name='hash_pair_4',
        on_delete=models.CASCADE,
        blank=True, null=True
    )
    date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Cross-Exchange Arbitrage'
        
    def __self__(self):
        return self.hash_pair
        
    def get_profit(self):
        pass
    
