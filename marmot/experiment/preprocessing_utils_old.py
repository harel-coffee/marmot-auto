from __future__ import print_function

import os
import sys
import copy
import multiprocessing as multi
import logging
import numpy as np
from collections import defaultdict
from sklearn.preprocessing.label import LabelBinarizer, MultiLabelBinarizer
import ipdb

from marmot.util.simple_corpus import SimpleCorpus
from marmot.experiment.import_utils import list_of_lists

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger('testlogger')


# convert alignments from list of strings 'i-j'
# to list of lists such that new_align[j] = i
def convert_alignments(align_list, n_words):
    new_align = [[] for i in range(n_words)]
    for pair in align_list:
        two_digits = pair.split('-')
        new_align[int(two_digits[1])].append(int(two_digits[0]))
    return new_align


# baseline strategy: duplicate each sentence N times (N - number of words in the sentence)
def multiply_data_base(representations):
    partial = {a_key: [] for a_key in representations}
    # loop through sentences 
    for idx in range(len(representations['target'])):
        if 'source' in representations:
            partial['source'].append(representations['source'][idx])
        if 'alignments' in representations:
            partial['alignments'].append(representations['alignments'][idx])
        if 'target_pos' in representations:
            partial['target_pos'].append(representations['target_pos'][idx])
        if 'source_pos' in representations:
            partial['source_pos'].append(representations['source_pos'][idx])
        if 'pseudo_ref' in representations:
            partial['pseudo_ref'].append(representations['pseudo_ref'][idx])
        if 'tags' in representations:
            partial['tags'].append(representations['tags'][idx])
        partial['target'].append(representations['target'][idx])
    return partial


# create sequences consisting of the first 1, 2, 3, ..., N words for every original sequence
# borders -- create a representation that contains markers of borders:
#   'SE' - Start-End (full sentence)
#   'SN' - Start-Not-end (partial sentence)
def multiply_data(representations, borders=False):
    partial = {a_key: [] for a_key in representations}
    if borders:
        partial['borders'] = []
    # loop through sentences 
    for idx in range(len(representations['target'])):
        # loop through words in the sentence
        for w_idx in range(len(representations['target'][idx])):
            if 'source' in representations:
                partial['source'].append(representations['source'][idx])
            if 'alignments' in representations:
                partial['alignments'].append(representations['alignments'][idx][:w_idx+1])
            if 'alignments_all' in representations:
                partial['alignments_all'].append(representations['alignments_all'][idx][:w_idx+1])
            if 'target_pos' in representations:
                partial['target_pos'].append(representations['target_pos'][idx][:w_idx+1])
            if 'source_pos' in representations:
                partial['source_pos'].append(representations['source_pos'][idx])
            if 'pseudo_ref' in representations:
                partial['pseudo_ref'].append(representations['pseudo_ref'][idx])
            if 'tags' in representations:
                partial['tags'].append(representations['tags'][idx][:w_idx+1])
            partial['target'].append(representations['target'][idx][:w_idx+1])

            if borders:
                if w_idx + 1 == len(representations['target']):
                    partial['borders'].append('SE')
                else:
                    partial['borders'].append('SN')
    return partial


# create sequences consisting of all ngrams of every original sequence
# :param order: -- order of ngram
# borders -- create a representation that contains markers of borders:
#   'SE' - Start-End (full sentence)
#   'SN' - Start-Not-end (partial sentence)
#   'NE' - Not-start-End 
#   'NN' - Not-start-Not-end
def multiply_data_ngrams(representations, order=3, borders=False):
    partial = {a_key: [] for a_key in representations}
    if borders:
        partial['borders'] = []
    # loop through sentences 
    for idx in range(len(representations['target'])):
        # loop through words in the sentence
        for w_idx in range(len(representations['target'][idx])):
            start = max(0, w_idx - order + 1)
            end = w_idx + 1
            if 'source' in representations:
                partial['source'].append(representations['source'][idx])
            if 'alignments' in representations:
                partial['alignments'].append(representations['alignments'][idx][start:end])
            if 'target_pos' in representations:
                partial['target_pos'].append(representations['target_pos'][idx][start:end])
            if 'source_pos' in representations:
                partial['source_pos'].append(representations['source_pos'][idx])
            if 'pseudo_ref' in representations:
                partial['pseudo_ref'].append(representations['pseudo_ref'][idx])
            if 'tags' in representations:
                partial['tags'].append(representations['tags'][idx][start:end])
            partial['target'].append(representations['target'][idx][start:end])
            if borders:
                border_start, border_end = '', ''
                if start == 0:
                    border_start = 'S'
                else:
                    border_start = 'N'
                if end == len(representations['target']):
                    border_end = 'E'
                else:
                    border_end = 'N'
                partial['borders'].append(border_start + border_end)
    return partial


# take all substrings of a string
def multiply_data_all(representations, borders=False):
    partial = {a_key: [] for a_key in representations}
    if borders:
        partial['borders'] = []
    # loop through sentences 
    for idx in range(len(representations['target'])):
        # loop through words in the sentence
        for w_idx in range(len(representations['target'][idx])):
            if 'source' in representations:
                partial['source'].append(representations['source'][idx])
            if 'alignments' in representations:
                partial['alignments'].append(representations['alignments'][idx][:w_idx+1])
            if 'target_pos' in representations:
                partial['target_pos'].append(representations['target_pos'][idx][:w_idx+1])
            if 'source_pos' in representations:
                partial['source_pos'].append(representations['source_pos'][idx])
            if 'pseudo_ref' in representations:
                partial['pseudo_ref'].append(representations['pseudo_ref'][idx])
            if 'tags' in representations:
                partial['tags'].append(representations['tags'][idx][:w_idx+1])
            partial['target'].append(representations['target'][idx][:w_idx+1])
            if borders:
                if w_idx + 1 == len(representations['target']):
                    partial['borders'].append('SE')
                else:
                    partial['borders'].append('SN')
#            if borders:
#                border_start, border_end = '', ''
#                if start == 0:
#                    border_start = 'S'
#                else:
#                    border_start = 'N'
#                if end == len(representations['target']):
#                    border_end = 'E'
#                else:
#                    border_end = 'N'
#                partial['borders'].append(border_start + border_end)
            # substrings that don't start from the first word
            if w_idx > 0:
                for w2_idx in range(1, w_idx):
                    if 'source' in representations:
                        partial['source'].append(representations['source'][idx])
                    if 'alignments' in representations:
                        partial['alignments'].append(representations['alignments'][idx][w2_idx:w_idx+1])
                    if 'target_pos' in representations:
                        partial['target_pos'].append(representations['target_pos'][idx][w2_idx:w_idx+1])
                    if 'source_pos' in representations:
                        partial['source_pos'].append(representations['source_pos'][idx])
                    if 'pseudo_ref' in representations:
                        partial['pseudo_ref'].append(representations['pseudo_ref'][idx])
                    if 'tags' in representations:
                        partial['tags'].append(representations['tags'][idx][w2_idx:w_idx+1])
                    partial['target'].append(representations['target'][idx][w2_idx:w_idx+1])
                    if borders:
                        border_start, border_end = '', ''
                        if w2_idx == 0:
                            border_start = 'S'
                        else:
                            border_start = 'N'
                        if w_idx + 1  == len(representations['target']):
                            border_end = 'E'
                        else:
                            border_end = 'N'
                        partial['borders'].append(border_start + border_end)
    return partial


# TODO: this function adds keys to the context object, but maybe the user wants different keys
# TODO: the function should be agnostic about which keys it adds -- why does it care?
# there is a difference between 'sequence fields' and 'token fields'
# this method creates a context for each token
def create_context(repr_dict, sentence_id=None):
    '''
    :param repr_dict: a dict representing a 'line' or 'sentence' or a 'segment'
    :return: a list of context objects representing the data for each token in the sequence
    '''

    context_list = []
    # is checked before in create_contexts, but who knows
    if 'target' not in repr_dict:
        print("No 'target' label in data representations")
        return []
    if 'tags' not in repr_dict:
        print("No 'tag' label in data representations or wrong format of tag")
        print(repr_dict)
        return []
#    if 'alignments' in repr_dict:
#        repr_dict['alignments'] = convert_alignments(repr_dict['alignments'], len(repr_dict['target']))

    active_keys = repr_dict.keys()
    active_keys.remove('tags')
    for idx, word in enumerate(repr_dict['target']):
        c = {}
        c['token'] = word
        c['index'] = idx
        if sentence_id is not None:
            c['sentence_id'] = sentence_id
        if type(repr_dict['tags']) == list or type(repr_dict['tags']) == np.ndarray:
            c['tag'] = repr_dict['tags'][idx]
            c['sequence_tags'] = repr_dict['tags']
        elif type(repr_dict['tags']) == int:
            c['tag'] = repr_dict['tags'][idx]
        else:
            print("Unknown type of tags representation:", type(repr_dict['tags']))
            return []
        for k in active_keys:
            c[k] = repr_dict[k]
        context_list.append(c)
    return context_list


# create context objects from a data_obj -
#     - a dictionary with representation labels as keys ('target', 'source', etc.) and
#       representations (lists of lists) as values
# output: if data_type = 'plain', one list of context objects is returned
#         if data_type = 'sequential', a list of lists of context objects is returned (list of sequences)
#         if data_type = 'token', a dict {token: <list_of_contexts>} is returned
# TODO: this function requires the 'target' and 'tag' keys, but the user may wish to specify other keys
# TODO: 'target' and 'tag' don't make sense for every task
def create_contexts(data_obj, data_type='plain'):
    '''
    :param data_obj: an object representing a dataset consisting of files
    :param data_type:
    :return:
    '''
    contexts = []
    if 'target' not in data_obj:
        print("No 'target' label in data representations")
        return []

    if 'tags' not in data_obj:
        print("No 'tag' label in data representations or wrong format of tag")
        return []

    for s_idx, sents in enumerate(zip(*data_obj.values())):
        if data_type == 'sequential':
#            print(contexts)
            contexts.append(create_context({data_obj.keys()[i]: sents[i] for i in range(len(sents))}, sentence_id=s_idx))
        else:
            contexts.extend(create_context({data_obj.keys()[i]: sents[i] for i in range(len(sents))}, sentence_id=s_idx))

            # TODO: there is an error here
            if data_type == 'token':
                new_contexts = defaultdict(list)
                for cont in contexts:
                    new_contexts[cont['token']].append(cont)
                    contexts = copy.deepcopy(new_contexts)

    return contexts


# convert list of lists into a flat list
# TODO: there is an error where no code runs here
def flatten(lofl):
    if list_of_lists(lofl):
        return [item for sublist in lofl for item in sublist]
    elif type(lofl) == dict:
        return lofl.values()


def map_feature_extractor((context, extractor)):
    return extractor.get_features(context)


def map_feature_extractors((sequence, extractors)):
    features = []
    for obj in sequence:
        obj_features = []
        for extractor in extractors:
            obj_features.extend(extractor.get_features(obj))
        features.append(obj_features)
    return features


# feature extraction for categorical features with conversion to one-hot representation
# this implementation is for a list representation
# this returns a list of lists, where each list contains the feature extractor results for a context
# the point of returning a list of lists is to allow binarization of the feature values
# TODO: we can binarize over the columns of the matrix instead of binarizing the results of each feature extractor
# TODO: is the output of the single worker and the multithreaded different? if so, change
def contexts_to_features(contexts, feature_extractors, workers=1):
    return [[x for a_list in [map_feature_extractor((context, extractor)) for extractor in feature_extractors] for x in a_list] for context in contexts]


def contexts_to_features_multi(contexts, feature_extractors, workers=1):
#    print("One context:", contexts[0])
    # single thread
    if workers == 1:
#        print("Extractors:", type(feature_extractors))
#        print("Contexts:", type(contexts))
        #context = contexts[0]
#        all_return = []
#        for extractor in feature_extractors:
#            print("Extracting features with {}".format(extractor))
#            aaa = [map_feature_extractor((context, extractor)) for context in contexts]
#        for context in contexts:
#            aaa = [map_feature_extractor((context, extractor)) for extractor in feature_extractors]
#            all_return.append(x for a_list in aaa for x in a_list)
#            print("Context:", type(aaa[0][0]))
#            print("One context:", aaa[0])
#        return all_return
#        return [[x for a_list in [map_feature_extractor((context, extractor)) for extractor in feature_extractors] for x in a_list] for context in contexts]
        return [[x for a_list in [map_feature_extractor((context, extractor)) for extractor in feature_extractors] for x in a_list] for context in contexts]

    # multiple threads
    else:
        # resulting object
        res_list = []
        #ipdb.set_trace()
        pool = multi.Pool(workers)
        logger.info('Multithreaded - Extracting the features for: ' + str(len(contexts)) + ' contexts...')
        # each context is paired with all feature extractors
        for extractor in feature_extractors:
            context_list = [(cont, extractor) for cont in contexts]
#            print("Contexts:", contexts)
#            sys.exit()
#            print("Types: ", [(type(x), type(context_list[0][0][x])) for x in context_list[0][0]])
#            print("Values: ", [(x, context_list[0][0][x]) for x in context_list[0][0]])
            #ipdb.set_trace()
            features = pool.map(map_feature_extractor, context_list)
            res_list.append(features)
        # np.hstack and np.vstack can't be used because lists have objects of different types
        intermediate = [[x[i] for x in res_list] for i in range(len(res_list[0]))]
        res_list = [flatten(x) for x in intermediate]
        pool.close()
        pool.join()

    return res_list


def contexts_to_features_seq(contexts, feature_extractors, workers=1):

    res_list = []
    #ipdb.set_trace()
    pool = multi.Pool(workers)
    logger.info('Multithreaded - Extracting the features for: ' + str(len(contexts)) + ' contexts...')
    # each context is paired with all feature extractors
    flat_contexts = flatten(contexts)
    seq_lengths = [len(seq) for seq in contexts]
    for extractor in feature_extractors:
        context_list = [(cont, extractor) for cont in flat_contexts]
        #ipdb.set_trace()
        features = pool.map(map_feature_extractor, context_list)
        res_list.append(features)
    # np.hstack and np.vstack can't be used because lists have objects of different types
    intermediate = [[x[i] for x in res_list] for i in range(len(res_list[0]))]
    res_list = [flatten(x) for x in intermediate]
    cnt = 0
    seq_res = []
    for seq in seq_lengths:
        seq_res.append(res_list[cnt:cnt+seq])
        cnt += seq
    pool.close()
    pool.join()

    return seq_res


#    pool = multi.Pool(workers)
#    context_list = [(sequence, feature_extractors) for sequence in contexts]
#    features = pool.map(map_feature_extractors, context_list)
#    pool.close()
#    pool.join()
#    return features


# extract tags from a list of contexts
def tags_from_contexts(contexts):
    return [context['tag'] for context in contexts]


# train converters(binarizers) from categorical values to one-hot representation
#      for all features
# all_values is a list of lists, because we need to look at the feature values for every instance to binarize properly
def fit_binarizers(all_values):
    binarizers = {}
    for f in range(len(all_values[0])):
        cur_features = [context[f] for context in all_values]
        # only categorical values need to be binarized, ints/floats are left as they are
        if type(cur_features[0]) == str or type(cur_features[0]) == unicode:
            lb = LabelBinarizer()
            lb.fit(cur_features)
            binarizers[f] = lb
        elif type(cur_features[0]) == list:
            mlb = MultiLabelBinarizer()
            # default feature for unknown values
            cur_features.append(tuple(("__unk__",)))
            mlb.fit([tuple(x) for x in cur_features])
            binarizers[f] = mlb
    return binarizers


# convert categorical features to one-hot representations with pre-fitted binarizers
# TODO: this function implicitly converts the data into a numpy array
def binarize(features, binarizers):
    assert(list_of_lists(features))
    num_features = len(features[0])
#    if binarizers != {} and max(binarizers.keys()) >= num_features:     
#        print("Binarizers keys max: ", max(binarizers.keys()))
#        print("Total feature number: ", num_features)
#        print("Features:", features[0])
    assert(binarizers == {} or max(binarizers.keys()) < num_features)

    binarized_cols = []
    for i in range(num_features):
        # get this column
        cur_values = [f[i] for f in features]
        # if there's a binarizer for this column
        if i in binarizers:
            binarizer = binarizers[i]
            if type(binarizer) == LabelBinarizer:
                try:
                    binarized_cols.append(binarizer.transform(cur_values))
                except:
                    pass
#                    print(cur_values)
            elif type(binarizer) == MultiLabelBinarizer:
                assert(list_of_lists(cur_values))
                # MultiLabelBinarizer doesn't support unknown values -- they need to be replaced with a default value
                # we're going to use the empty list as the default value
                cur_values_default = []
                default_value = binarizer.classes_[-1]
                for a_list in cur_values:
                    new_list = list(a_list)
                    for j, val in enumerate(new_list):
                        if val not in binarizer.classes_:
                            new_list[j] = default_value
                    cur_values_default.append(tuple(new_list))

                transformed = binarizer.transform(cur_values_default)
                binarized_cols.append(transformed)
            else:
                raise NotImplementedError('this function is not implemented for type: {}'.format(type(binarizer)))
        else:
#            arr = np.array(cur_values)
#            print(arr.shape)
#            print(len(cur_values))
#            print(cur_values)
            try:
#                new_vals = np.array(cur_values).reshape(len(cur_values), 1)
                binarized_cols.append(np.array(cur_values).reshape(len(cur_values), 1))
            except:
                print(cur_values)
                sys.exit()

    assert (len(binarized_cols) == num_features), 'the number of columns after binarization must match the number of features'
    new_features = np.hstack(binarized_cols)

    return new_features
