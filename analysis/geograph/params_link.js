//----------------------------------------------------------------------------
// VALUES TO CHANGE PER FIGURE

// scaleFactor: 1 = saturate only at max; 10 = saturate at 1/10 of max.
// There's generally an outlier, so increasing to 2, 3, ... so that a few
// values saturate improves low-end resolution.
var scaleFactor = 100;

// metric_type:  one in ['seq', 'div'] for sequential or divergent.
var metric_type = 'seq';
