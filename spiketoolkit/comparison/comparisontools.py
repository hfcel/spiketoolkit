"""
Some functions internally use by SortingComparison.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment



def count_matching_events(times1, times2, delta=10):
    times_concat = np.concatenate((times1, times2))
    membership = np.concatenate((np.ones(times1.shape) * 1, np.ones(times2.shape) * 2))
    indices = times_concat.argsort()
    times_concat_sorted = times_concat[indices]
    membership_sorted = membership[indices]
    diffs = times_concat_sorted[1:] - times_concat_sorted[:-1]
    inds = np.where((diffs <= delta) & (membership_sorted[0:-1] != membership_sorted[1:]))[0]
    if (len(inds) == 0):
        return 0
    inds2 = np.where(inds[:-1] + 1 != inds[1:])[0]
    return len(inds2) + 1



def compute_agreement_score(num_matches, num1, num2):
    """
    Agreement score is used as a criteria to match unit1 and unit2.
    """
    denom = num1 + num2 - num_matches
    if denom == 0:
        return 0
    return num_matches / denom


def do_matching(sorting1, sorting2, delta_tp, min_accuracy):
    """
    This compute the matching between 2 sorters.
    
    Parameters
    ----------
    sorting1: SortingExtractor instance
    
    sorting2: SortingExtractor instance
    
    delta_tp: int
    
    
    Output
    ----------
    
    event_counts_1:
    
    event_counts_2
    
    matching_event_counts_12:
    
    best_match_units_12:
    
    matching_event_counts_21:
    
    best_match_units_21:
    
    unit_map12:
    
    unit_map21:

    
    """
    event_counts_1 = dict()
    event_counts_2 = dict()
    matching_event_counts_12 = dict()
    best_match_units_12 = dict()
    matching_event_counts_21 = dict()
    best_match_units_21 = dict()
    unit_map12 = dict()
    unit_map21 = dict()

    unit1_ids = sorting1.getUnitIds()
    unit2_ids = sorting2.getUnitIds()
    N1 = len(unit1_ids)
    N2 = len(unit2_ids)
    
    # Compute events counts
    event_counts1 = np.zeros((N1)).astype(np.int64)
    for i1, u1 in enumerate(unit1_ids):
        times1 = sorting1.getUnitSpikeTrain(u1)
        event_counts1[i1] = len(times1)
        event_counts_1[u1] = len(times1)
    event_counts2 = np.zeros((N2)).astype(np.int64)
    for i2, u2 in enumerate(unit2_ids):
        times2 = sorting2.getUnitSpikeTrain(u2)
        event_counts2[i2] = len(times2)
        event_counts_2[u2] = len(times2)

    # Compute matching events
    matching_event_counts = np.zeros((N1, N2)).astype(np.int64)
    scores = np.zeros((N1, N2))
    for i1, u1 in enumerate(unit1_ids):
        times1 = sorting1.getUnitSpikeTrain(u1)
        for i2, u2 in enumerate(unit2_ids):
            times2 = sorting2.getUnitSpikeTrain(u2)
            num_matches = count_matching_events(times1, times2, delta=delta_tp)
            matching_event_counts[i1, i2] = num_matches
            scores[i1, i2] = compute_agreement_score(num_matches, event_counts1[i1], event_counts2[i2])

    # Find best matches for spiketrains 1
    for i1, u1 in enumerate(unit1_ids):
        scores0 = scores[i1, :]
        matching_event_counts_12[u1] = dict()
        if len(scores0)>0:
            if np.max(scores0) > 0:
                inds0 = np.where(scores0 > 0)[0]
                for i2 in inds0:
                    matching_event_counts_12[u1][unit2_ids[i2]] = matching_event_counts[i1, i2]
                i2_best = np.argmax(scores0)
                best_match_units_12[u1] = unit2_ids[i2_best]
            else:
                best_match_units_12[u1] = -1
        else:
            best_match_units_12[u1] = -1

    # Find best matches for spiketrains 2
    for i2, u2 in enumerate(unit2_ids):
        scores0 = scores[:, i2]
        matching_event_counts_21[u2] = dict()
        if len(scores0)>0:
            if np.max(scores0) > 0:
                inds0 = np.where(scores0 > 0)[0]
                for i1 in inds0:
                    matching_event_counts_21[u2][unit1_ids[i1]] = matching_event_counts[i1, i2]
                i1_best = np.argmax(scores0)
                best_match_units_21[u2] = unit1_ids[i1_best]
            else:
                best_match_units_21[u2] = -1
        else:
            best_match_units_21[u2] = -1

    # Assign best matches
    [inds1, inds2] = linear_sum_assignment(-scores)
    inds1 = list(inds1)
    inds2 = list(inds2)
    if len(unit2_ids)>0:
        k2 = np.max(unit2_ids) + 1
    else:
        k2 = 1
    for i1, u1 in enumerate(unit1_ids):
        if i1 in inds1:
            aa = inds1.index(i1)
            i2 = inds2[aa]
            u2 = unit2_ids[i2]
            # criteria on agreement_score
            num_matches = matching_event_counts_12[u1].get(u2, 0)
            num1 = event_counts_1[u1]
            num2 = event_counts_2[u2]
            agree_score = compute_agreement_score(num_matches, num1, num2)
            if agree_score > min_accuracy:
                unit_map12[u1] = u2
            else:
                unit_map12[u1] = -1
        else:
            # unit_map12[u1] = k2
            # k2 = k2+1
            unit_map12[u1] = -1
    if len(unit1_ids)>0:
        k1 = np.max(unit1_ids) + 1
    else:
        k1 = 1
    for i2, u2 in enumerate(unit2_ids):
        if i2 in inds2:
            aa = inds2.index(i2)
            i1 = inds1[aa]
            u1 = unit1_ids[i1]
            # criteria on agreement_score
            num_matches = matching_event_counts_12[u1].get(u2, 0)
            num1 = event_counts_1[u1]
            num2 = event_counts_2[u2]
            agree_score = compute_agreement_score(num_matches, num1, num2)
            if agree_score > min_accuracy:
                unit_map21[u2] = u1
            else:
                unit_map21[u2] = -1
        else:
            # unit_map21[u2] = k1
            # k1 = k1+1
            unit_map21[u2] = -1
    
    return (event_counts_1,  event_counts_2,
                matching_event_counts_12, best_match_units_12,
                matching_event_counts_21,  best_match_units_21, 
                unit_map12,  unit_map21)





    
def do_counting(sorting1, sorting2, delta_tp, unit_map12):
    """
    This count all counting score possible lieke:
      * TP: true positive
      * CL: classification error
      * FN: False negative
      * FP: False positive
      * TOT: 
      * TOT_ST1: 
      * TOT_ST2: 

    Parameters
    ----------
    sorting1: SortingExtractor instance
        The ground truth sorting.
    
    sorting2: SortingExtractor instance
        The tested sorting.
    
    delta_tp: int
        
    unit_map12: dict
        Dict of matching from sorting1 to sorting2.

    Output
    ----------
    
    counts: dict 
        A dict containing all coutning
    
    labels_st1: np.array of str
        Contain label for units of sorting 1
    
    labels_st2: np.array of str
        Contain label for units of sorting 2
    """
    
    unit1_ids = sorting1.getUnitIds()
    unit2_ids = sorting2.getUnitIds()
    labels_st1 = dict()
    labels_st2 = dict()
    N1 = len(unit1_ids)
    N2 = len(unit2_ids)

    # copy spike trains for faster access from extractors with memmapped data
    sts1 = []
    for u in sorting1.getUnitIds():
        sts1.append(sorting1.getUnitSpikeTrain(u))
    sts2 = []
    for u in sorting2.getUnitIds():
        sts2.append(sorting2.getUnitSpikeTrain(u))
    
    # Evaluate
    for i,u1 in enumerate(unit1_ids):
        lab_st1 = np.array(['UNPAIRED'] * len(sts1[i]))
        labels_st1[u1] = lab_st1
    for i,u2 in enumerate(unit2_ids):
        lab_st2 = np.array(['UNPAIRED'] * len(sts2[i]))
        labels_st2[u2] = lab_st2

    for u_i, u1 in enumerate(sorting1.getUnitIds()):
        u2 = unit_map12[u1]
        if u2 !=-1:
            lab_st1 = labels_st1[u1]
            lab_st2 = labels_st2[u2]
            mapped_st = sorting2.getUnitSpikeTrain(u2)
            # from gtst: TP, TPO, TPSO, FN, FNO, FNSO
            for sp_i, n_sp in enumerate(sts1[u_i]):
                matches = (np.abs(mapped_st.astype(int)-n_sp)<=delta_tp//2)
                if np.sum(matches) > 0:
                        lab_st1[sp_i] = 'TP'
                        lab_st2[np.where(matches)[0][0]] = 'TP'
        else:
            # Sam garcia note : I guess this is a mistake
            lab_st1 = np.array(['FN'] * len(sts1[u_i]))
            # Sam note : I would add this line
            # labels_st1[u1] = lab_st1

    # find CL-CLO-CLSO
    for u_i, u1 in enumerate(sorting1.getUnitIds()):
        lab_st1 = labels_st1[u1]
        #~ st1 = sorting1.getUnitSpikeTrain(u1)
        st1 = sts1[u_i]
        for l_gt, lab in enumerate(lab_st1):
            if lab == 'UNPAIRED':
                for u_j, u2 in enumerate(sorting2.getUnitIds()):
                    if u2 in unit_map12.values() and unit_map12[u1] != -1:
                        lab_st2 = labels_st2[u2]
                        st2 = sts2[u_j]

                        n_up = st1[l_gt]
                        id_sp = np.where((st2.astype(int)-n_sp)<=delta_tp//2)[0]
                        if len(id_sp) > 0 and lab_st2[id_sp[0]] == 'UNPAIRED':
                            lab_st1[l_gt] = 'CL_' + str(u1) + '_' + str(u2)
                            lab_st2[id_sp[0]] = 'CL_' + str(u2) + '_' + str(u1)

    for u1 in sorting1.getUnitIds():
        lab_st1 = labels_st1[u1]
        for l_gt, lab in enumerate(lab_st1):
            if lab == 'UNPAIRED':
                lab_st1[l_gt] = 'FN'

    for u2 in sorting2.getUnitIds():
        lab_st2 = labels_st2[u2]
        for l_gt, lab in enumerate(lab_st2):
            if lab == 'UNPAIRED':
                lab_st2[l_gt] = 'FP'

    TOT_ST1 = sum([len(sts1[i]) for i in range(len(sts1))])
    TOT_ST2 = sum([len(sts2[i]) for i in range(len(sts2))])
    total_spikes = TOT_ST1 + TOT_ST2
    TP = sum([len(np.where('TP' == labels_st1[unit])[0]) for unit in sorting1.getUnitIds()])
    CL = sum(
        [len([i for i, v in enumerate(labels_st1[unit]) if 'CL' in v]) for unit in sorting1.getUnitIds()])
    FN = sum([len(np.where('FN' == labels_st1[unit])[0]) for unit in sorting1.getUnitIds()])
    FP = sum([len(np.where('FP' == labels_st2[unit])[0]) for unit in sorting2.getUnitIds()])
    
    counts = {'TP': TP, 'CL': CL, 'FN': FN, 'FP': FP, 'TOT': total_spikes, 'TOT_ST1': TOT_ST1,
                   'TOT_ST2': TOT_ST2}

    return counts, labels_st1, labels_st2
    


def do_confusion_matrix(sorting1, sorting2, unit_map12, labels_st1, labels_st2):
    """
    Compute the confusion matrix between two sorting.
    
    Parameters
    ----------
    sorting1: SortingExtractor instance
        The ground truth sorting.
    
    sorting2: SortingExtractor instance
        The tested sorting.

    unit_map12: dict
        Dict of matching from sorting1 to sorting2.
        

    Output
    ----------
    
    confusion_matrix: the confusion matrix
    
    st1_idxs: ???
    
    st2_idxs: ???
    
    
    """

    unit1_ids = np.array(sorting1.getUnitIds())
    unit2_ids = np.array(sorting2.getUnitIds())
    N1 = len(unit1_ids)
    N2 = len(unit2_ids)
    
    conf_matrix = np.zeros((N1 + 1, N2 + 1), dtype=int)
    
    mapped_units = np.array(list(unit_map12.values()))
    idxs_matched, = np.where(mapped_units != -1)
    idxs_unmatched, = np.where(mapped_units == -1)
    unit_map_matched = mapped_units[idxs_matched]

    st1_idxs =np.hstack([unit1_ids[idxs_matched], unit1_ids[idxs_unmatched]])
    st2_matched = unit_map_matched
    st2_unmatched = []

    for u_i, u1 in enumerate(unit1_ids[idxs_matched]):
        lab_st1 = labels_st1[u1]
        tp = len(np.where('TP' == lab_st1)[0])
        conf_matrix[u_i, u_i] = int(tp)
        for u_j, u2 in enumerate(unit2_ids):
            lab_st2 = labels_st2[u2]
            cl_str = str(u1) + '_' + str(u2)
            cl = len([i for i, v in enumerate(lab_st1) if 'CL' in v and cl_str in v])
            if cl != 0:
                st_p, = np.where(u2 == unit_map_matched)
                conf_matrix[u_i, st_p] = int(cl)
        fn = len(np.where('FN' == lab_st1)[0])
        conf_matrix[u_i, -1] = int(fn)

    for u_i, u1 in enumerate(unit1_ids[idxs_unmatched]):
        lab_st1 = labels_st1[u1]
        fn = len(np.where('FN' == lab_st1)[0])
        conf_matrix[u_i + len(idxs_matched), -1] = int(fn)

    for u_j, u2 in enumerate(unit2_ids):
        lab_st2 = labels_st2[u2]
        fp = len(np.where('FP' == lab_st2)[0])
        st_p, = np.where(u2 == unit_map_matched)
        if len(st_p) != 0:
            conf_matrix[-1, st_p] = int(fp)
        else:
            st2_unmatched.append(int(u2))
            conf_matrix[-1, len(idxs_matched) + len(st2_unmatched) - 1] = int(fp)
    
    st2_idxs = np.hstack([st2_matched, st2_unmatched]).astype('int64')

    return conf_matrix,  st1_idxs, st2_idxs
    
    