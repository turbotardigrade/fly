import json
import numpy as np
from sklearn import cluster

def analyze(raw_data):
    data = json.loads(raw_data)['locations']
    data_size = len(data)
    print("# of locations %d" % data_size)

    reduceByFactor = 10
    locations = [None for _ in xrange(data_size/reduceByFactor+1)]

    # Reduce the data size
    j = 0
    for i in xrange(0, data_size, reduceByFactor):
        loc = data[i]
        lat, lon= int(loc['latitudeE7']), int(loc['longitudeE7'])
        locations[j] = [lat, lon]
        j += 1

    locations = filter(lambda x: x is not None, locations)
        
    # Use K-Mean clustering to get k hotspots
    k = 20
    kmeans = cluster.KMeans(n_clusters=k, n_jobs=2)
    data = np.array(locations, np.int32)
    kmeans.fit(data)

    points = []
    for centroid in kmeans.cluster_centers_:
        points.append({
            "lat": centroid[0]*1e-7,
            "lng": centroid[1]*1e-7
        })

    labels = []
    for count in np.bincount(kmeans.labels_):
        labels.append(float(count)/len(data)*100)

    result = []
    for l, p in zip(labels, points):
        result.append({"position": p, "label": round(l,2)})
    result.sort(key=lambda x: x["label"], reverse=True)

    # print results
    for r in result:
        print("position: {0}, label: {1}".format(r["label"], r["position"]))

    return result, data_size
