#!/usr/bin/env python
import argparse
import numpy as np
import awkward as ak
from typing import Callable
import uproot
import uproot.writing
from coffea.nanoevents import NanoEventsFactory
from coffea.nanoevents import DelphesSchema
from coffea.nanoevents.methods import delphes
import tqdm

def get_daughters(particle,
                  particle_array
):
    """
    """
    return particle_array[particle.D1: particle.D2 + 1]


def get_last(particle,
             particle_array,
             condition_fn: Callable[[delphes.Particle], bool] = lambda _: True
):
    last = particle
    while condition_fn(last):
        daughter_list = particle_array[last.D1: last.D2 + 1]
        num_daughters = len(daughter_list)
        if num_daughters == 1:
            daughter = daughter_list[0]
            if last.PID == daughter.PID:
                last = daughter
                continue
            else:
                raise RuntimeError
        elif num_daughters == 2:
            d0, d1 = daughter_list
            if last.PID == d0.PID:
                last = d0
                continue
            elif last.PID == d1.PID:
                last = d1
                continue
            else:
                break
        else:
            break

    return last

def convert_particle_list_to_array(particle_list):
    data = {field.lower(): [getattr(each, field) for each in particle_list]
            for field in particle_list[0].fields
            if field not in ['fBits']}

    renaming = {'e': 'energy'}
    data = {renaming.get(key, key): value
            for key, value in data.items()}
    return ak.Array(data)

def get_top_daughters(top, particle_array):
    daughters = get_daughters(top, particle_array)
    if abs(daughters[0].PID) == 5: # b quark
        b, w = daughters
    else:
        w, b = daughters
    return b, w

def find_partons(event) -> list[delphes.Particle]:
    top_mask = (abs(event.Particle.PID) == 6) & (event.Particle.Status == 62)
    # t and tbar
    t_p, t_m = event.Particle[top_mask]
    if t_p.PID == -6:
        t_p, t_m = t_m, t_p

    # b quark and W+
    b_m, w_p = get_top_daughters(t_p, event.Particle)

    # anti b quark and W-
    b_p, w_m = get_top_daughters(t_m, event.Particle)

    b_m = get_last(b_m, event.Particle,
                   condition_fn=lambda last: last.Status != 23) # type: ignore
    b_p = get_last(b_p, event.Particle,
                   condition_fn=lambda last: last.Status != 23) # type: ignore

    # t -> W+ (-> q0, q1), b-
    # t- -> W- (-> q2, q3), b+
    q0, q1 = get_daughters(get_last(w_p, event.Particle), event.Particle)
    q2, q3 = get_daughters(get_last(w_m, event.Particle), event.Particle)

    q0, q1, q2, q3 = [get_last(quark, event.Particle,
                               condition_fn=lambda last: last.Status != 23)
                      for quark in [q0, q1, q2, q3]]

    return [b_m, q0, q1, b_p, q2, q3]

def _perform_jet_parton_matching(parton_list: list[delphes.ParticleRecord], # type: ignore
                                 jet_list: delphes.JetArray, # type: ignore
                                 max_distance: float = 0.3
) -> dict[int, int]:
    distance_idx_list: list[tuple[float, int, int]] = []

    for parton_idx, parton in enumerate(parton_list):
        for jet_idx, jet in enumerate(jet_list):
            distance = parton.delta_r(jet)

            distance_idx_list.append((distance, parton_idx, jet_idx))

    distance_idx_list = sorted(distance_idx_list)

    match: dict[int, int] = {}
    while len(match) < len(parton_list):
        distance, parton_idx, jet_idx = distance_idx_list[0]
        if distance > max_distance:
            jet_idx = -1
        match[parton_idx] = jet_idx

        # remove
        idx = 0
        while idx < len(distance_idx_list):
            _, other_parton_idx, other_jet_idx = distance_idx_list[idx]
            if parton_idx == other_parton_idx or jet_idx == other_jet_idx:
                distance_idx_list.pop(idx)
            else:
                idx += 1
    return match

def perform_jet_parton_matching(event_arr, jet_arr_arr):
    parton_arr_arr = [find_partons(each)
                      for each
                      in tqdm.tqdm(event_arr, desc='finding partons')]

    parton2jet_arr = [
        _perform_jet_parton_matching(
            parton_list=parton_arr,
            jet_list=jet_arr,
        )
        for parton_arr, jet_arr
        in tqdm.tqdm(zip(parton_arr_arr, jet_arr_arr),
                     total=len(event_arr),
                     desc='running jet-parton matching')
    ]
    jet2parton_arr: list[dict[int, int]] = [
        {jet: parton for parton, jet in parton2jet.items()}
        for parton2jet in parton2jet_arr
    ]

    jet_parton_match_arr = [
        [jet2parton.get(jet, -1) for jet in range(len(jet_arr))]
        for jet2parton, jet_arr in zip(jet2parton_arr, jet_arr_arr)
    ]

    jet_parton_match_mask = np.array([-1 not in each.values()
                                      for each in parton2jet_arr])
    return ak.Array(jet_parton_match_arr), jet_parton_match_mask


def run(input_path, output_path):
    print(f'reading {input_path}')
    event_arr = NanoEventsFactory.from_root(
        file=input_path,
        treepath='Delphes',
        schemaclass=DelphesSchema
    ).events()


    total = len(event_arr)

    ###########################################################################
    # jet selection
    ###########################################################################
    print('running jet selection')
    jet_arr_arr = event_arr.Jet

    jet_mask = (
        (jet_arr_arr.PT > 30) &
        (abs(jet_arr_arr.Eta) < 2.4)
    )
    jet_arr_arr = jet_arr_arr[jet_mask]

    ###########################################################################
    # jet cut
    ###########################################################################
    print('applying jet multiplicity cut', end='')
    jet_cut = ak.sum(jet_mask, axis=1) >= 6

    event_arr = event_arr[jet_cut]
    jet_arr_arr = jet_arr_arr[jet_cut]

    print(f' -> eff = {len(event_arr)} / {total}'
          f' = {100 * len(event_arr) / total:.2f} %')

    ###########################################################################
    # 6-th jet's $p_T$ > 40 GeV
    ###########################################################################
    print('applying 6th jet pt cut', end='')
    sixth_jet_cut = ak.sort(jet_arr_arr.PT, axis=1)[..., 5] > 40

    event_arr = event_arr[sixth_jet_cut]
    jet_arr_arr = jet_arr_arr[sixth_jet_cut]

    print(f' -> eff = {len(event_arr)} / {total}'
          f' = {100 * len(event_arr) / total:.2f} %')

    ###########################################################################
    # btag cut
    ###########################################################################
    print('applying b-tagged jet multiplicity cut', end='')
    btag_cut = ak.sum(jet_arr_arr.BTag, axis=1) >= 1

    event_arr = event_arr[btag_cut]
    jet_arr_arr = jet_arr_arr[btag_cut]

    print(f' -> eff = {len(event_arr)} / {total}'
          f' = {100 * len(event_arr) / total:.2f} %')

    ###########################################################################
    # ht cut
    ###########################################################################
    print('applying HT cut', end='')
    ht_arr = ak.sum(jet_arr_arr.pt, axis=1)
    ht_cut = ht_arr > 450

    event_arr = event_arr[ht_cut]
    jet_arr_arr = jet_arr_arr[ht_cut]

    print(f' -> eff = {len(event_arr)} / {total}'
          f' = {100 * len(event_arr) / total:.2f} %')
    ###########################################################################
    # jet-parton matching
    ###########################################################################
    jet_parton_match_arr, jet_parton_match_mask = perform_jet_parton_matching(
        event_arr, jet_arr_arr)

    event_arr = event_arr[jet_parton_match_mask]
    jet_arr_arr = jet_arr_arr[jet_parton_match_mask]
    jet_parton_match_arr = jet_parton_match_arr[jet_parton_match_mask]

    print('selecting matched events', end='')
    print(f' -> eff = {len(event_arr)} / {total}'
          f' = {100 * len(event_arr) / total:.2f} %')

    ###########################################################################
    # write
    ###########################################################################
    print(f'writing results to {output_path}')
    output = {
        'jet_pt': jet_arr_arr.PT,
        'jet_eta': jet_arr_arr.Eta,
        'jet_phi': jet_arr_arr.Phi,
        'jet_mass': jet_arr_arr.Mass,
        'jet_btag': jet_arr_arr.BTag,
        'jet_parton_match': jet_parton_match_arr,
    }

    for key, value in output.items():
        print(f'{key}: {value}')

    with uproot.writing.create(output_path) as output_file:
        output_file['tree'] = output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-path', required=True, type=str,
                        help='Help text')
    parser.add_argument('-o', '--output-path', required=True, type=str,
                        help='Help text')
    args = parser.parse_args()

    run(**vars(args))

if __name__ == "__main__":
    main()
