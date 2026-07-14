from natsort import natsort_keygen, ns

NATURAL_KEY = natsort_keygen(alg=ns.IGNORECASE)
