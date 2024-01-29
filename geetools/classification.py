"""Module for classification tools."""
import ee


def binaryRasterAccuracy(truth, classified, region=None):
    """Get a class raster with the following classes.

    band "classes":
    0: no change detected and no real change (true negative)
    1: no change detected but real change (false negative)
    2: change detected but not real change (false positive)
    3: change detected and real change (true positive)

    band "truth":
    0: no change
    1: change

    source: https://en.wikipedia.org/wiki/Evaluation_of_binary_classifiers

    For both `truth` and `classified` image input, it only uses the first
    band, therefore there is no need to specify a band.

    :param truth: binary image with ground truth. Only the first band will
        be used
    :type truth: ee.Image
    :param classified: classified binary image. Only the first band will
        be used
    :type classified: ee.Image
    :param region: region for clipping the truth and classified images
    :type region: ee.Geometry
    """
    # convert to int
    truth = truth.select([0]).toInt().unmask()
    classified = classified.select([0]).toInt().unmask()

    if region:
        truth = truth.clip(region)
        classified = classified.clip(region)

    final = (
        ee.Image()
        .expression(
            """
        t == 1 && c == 1 ? 3 :
        t == 0 && c == 1 ? 2 :
        t == 1 && c == 0 ? 1 : 0
        """,
            dict(t=truth, c=classified),
        )
        .rename("classes")
    )

    return final


def binaryMetrics(truth, classified, scale, region=None):
    """Get accuracy from a truth image and a classified image.

    names from: https://en.wikipedia.org/wiki/Evaluation_of_binary_classifiers

    :param truth: binary truth image. Only the first band will be used
    :type truth: ee.Image
    :param classified: the classification results. Only the first band will be
        used
    :type classified: ee.Image
    :param scale: the scale for the analysis
    :type scale: int
    :param region: the region for the analysis.
    :type region: ee.Geometry
    :return: a dictionary with the following
    TPR = True Positive Rate, recall or sensitivity
    TNR = True Negative Rate, selectivity or specificity
    PPV = Positive Predictive Value or precision
    NPV = Negative Predictive Value
    FNR = False Negative Rate or miss rate
    FPR = False Positive Rate or fall-out
    FDR = False Discovery Rate
    FOR = False Omission Rate
    TS = Threat score
    ACC = Accuracy
    BA = Balanced Accuracy
    F1 = F1 score
    :rtype: ee.ConfusionMatrix
    """
    class_list = ee.List(["0", "1", "2", "3"])
    names_list = ee.List(["TN", "FN", "FP", "TP"])

    scale = int(scale)

    classes = binaryRasterAccuracy(truth, classified, region)

    params = dict(
        reducer=ee.Reducer.frequencyHistogram(),
        scale=scale,
        maxPixels=int(1e13),
        tileScale=4,
    )
    if region:
        params["geometry"] = region

    # get frequency histogram (classes)
    matrix = classes.reduceRegion(**params)
    matrix = ee.Dictionary(matrix.get("classes"))  # cast

    def fillDict(clas, d):
        d = ee.Dictionary(d)
        clas = ee.String(clas)
        cond = d.contains(clas)
        return ee.Dictionary(ee.Algorithms.If(cond, d, d.set(clas, 0)))

    class_dict = ee.Dictionary(class_list.iterate(fillDict, matrix)).rename(class_list, names_list)

    TP = ee.Number(class_dict.get("TP"))
    TN = ee.Number(class_dict.get("TN"))
    FP = ee.Number(class_dict.get("FP"))
    FN = ee.Number(class_dict.get("FN"))

    ALL = dict(TP=TP, TN=TN, FP=FP, FN=FN)

    # Metrics
    TPR = ee.Number.expression("TP/(TP+FN)", ALL)
    TNR = ee.Number.expression("TN/(TN+FP)", ALL)
    PPV = ee.Number.expression("TP/(TP+FP)", ALL)
    NPV = ee.Number.expression("TN/(TN+FN)", ALL)
    FNR = ee.Number.expression("FN/(FN+TP)", ALL)
    FPR = ee.Number.expression("FP/(FP+TN)", ALL)
    FDR = ee.Number.expression("FP/(FP+TP)", ALL)
    FOR = ee.Number.expression("FN/(FN+TN)", ALL)
    TS = ee.Number.expression("TP/(TP+FN+FP)", ALL)
    ACC = ee.Number.expression("(TP+TN)/(TP+TN+FP+FN)", ALL)
    BA = ee.Number.expression("(TPR+TNR)/2", dict(TPR=TPR, TNR=TNR))
    F1 = ee.Number.expression("(2*TP)/(2*TP+FP+FN)", ALL)

    metrics = ee.Dictionary(
        dict(
            TPR=TPR,
            TNR=TNR,
            PPV=PPV,
            NPV=NPV,
            FNR=FNR,
            FPR=FPR,
            FDR=FDR,
            FOR=FOR,
            TS=TS,
            ACC=ACC,
            BA=BA,
            F1=F1,
        )
    )

    return class_dict.combine(metrics)
