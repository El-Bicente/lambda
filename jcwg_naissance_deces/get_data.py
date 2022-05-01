import json
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import dateutil as du
import pandas as pd


def get_data_from_url(url, as_str):
    data = urlopen(url)
    zipfile = ZipFile(BytesIO(data.read()))
    files = []
    with zipfile as f:
        for name in f.namelist():
            with f.open(name) as zd:
                files.append(
                    pd.read_csv(zd, delimiter=';', dtype={as_str: str}))
    return files[0]


def save_data_as_pkl(urlsn, urlsd):
    dfn = get_data_from_url(urlsn, 'DEPNAIS')
    dfd = get_data_from_url(urlsd, 'DEPDEC')

    dfn['date'] = dfn.apply(lambda x: convert_date(x.ANAIS, x.MNAIS), axis=1)
    dfn.set_index('date', inplace=True)

    dfd['date'] = dfd.apply(lambda x: convert_date(x.ADEC, x.MDEC), axis=1)
    dfd['AGE'] = dfd['ADEC'] - dfd['ANAIS']
    dfd.set_index('date', inplace=True)

    with open('data/jcwg_departements.geojson') as f:
        dep = json.load(f)

    dep_map = {d['properties']['code']: d['properties']['nom']
               for d in dep['features']}

    # Number of naissance/deces by department and date

    daten = dfn.groupby(['DEPNAIS', 'date']).size().rename(
        'SIZE').to_frame()
    dated = dfd.groupby(['DEPDEC', 'date']).size().rename(
        'SIZE').to_frame()

    # Number of naissance/deces by department

    depn = dfn.groupby('DEPNAIS').size().rename('SIZE').to_frame()
    depd = dfd.groupby('DEPDEC').size().rename('SIZE').to_frame()

    depn['NAME'] = [dep_map[d]
                    if d in dep_map else 'NON'
                    for d in depn.index]
    depd['NAME'] = [dep_map[d]
                    if d in dep_map else 'NON'
                    for d in depd.index]

    depn = depn.drop(depn[depn['NAME'] == 'NON'].index)
    depd = depd.drop(depd[depd['NAME'] == 'NON'].index)

    # Data about naissance/deces of men/women by their age

    agemn = dfn.groupby(['DEPNAIS', 'AGEMERE']).size().rename('SIZEMEREN')
    agepn = dfn.groupby(['DEPNAIS', 'AGEPERE']).size().rename('SIZEPEREN')

    agemd = dfd.loc[dfd.SEXE == 2, ['DEPDEC', 'AGE']].groupby(
        ['DEPDEC', 'AGE']).size().rename('SIZEMERED')
    agepd = dfd.loc[dfd.SEXE == 1, ['DEPDEC', 'AGE']].groupby(
        ['DEPDEC', 'AGE']).size().rename('SIZEPERED')

    agen = pd.concat([agemn, agepn, ], axis=1)
    agen['SIZEMEREPEREN'] = agen['SIZEMEREN'] + agen[
        'SIZEPEREN']
    agen['MGMEREPEREN'] = (agen['SIZEMEREN'] + agen[
        'SIZEPEREN']) // 2

    aged = pd.concat([agemd, agepd, ], axis=1)
    aged['SIZEMEREPERED'] = aged['SIZEMERED'] + aged[
        'SIZEPERED']
    aged['MGMEREPERED'] = (aged['SIZEMERED'] + aged[
        'SIZEPERED']) // 2

    # Save to csv

    daten.fillna(0).to_pickle('data/date_naissance.pkl')
    dated.fillna(0).to_pickle('data/date_deces.pkl')

    depn.fillna(0).to_pickle('data/department_naissance.pkl')
    depd.fillna(0).to_pickle('data/department_deces.pkl')

    agen.fillna(0).to_pickle('data/age_naissance.pkl')
    aged.fillna(0).to_pickle('data/age_deces.pkl')


def convert_date(y, m):
    return du.parser.parse(f"15-{m}-{y}")


if __name__ == '__main__':
    save_data_as_pkl(
        'https://www.insee.fr/fr/statistiques/fichier/4768335/etatcivil2019_nais2019_csv.zip',
        'https://www.insee.fr/fr/statistiques/fichier/4801913/etatcivil2019_dec2019_csv.zip')
    #
    # with open('data/jcwg_departements.geojson') as f:
    #     dep = json.load(f)
    #
    # dep_map = {d['properties']['code']: d['properties']['nom']
    #            for d in dep['features']}
    #
    # dfn = pd.read_pickle('data/naissance-2019.pkl')
    #
    # depn = dfn.groupby('DEPNAIS').size().rename('SIZE').to_frame()
    #
    # depn['NAME'] = [dep_map[d]
    #                 if d in dep_map else 'NON'
    #                 for d in depn.index]
    #
    # depn = depn.drop(depn[depn['NAME'] == 'NON'].index)
    # print(depn)
    # depn.to_pickle('data/test.csv')
    # print(pd.read_pickle('data/test.csv'))
