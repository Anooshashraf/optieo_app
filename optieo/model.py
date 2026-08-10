# model.py
import math

CONST = {'Re': 6371, 'mu': 398600.4418, 'h': 6.62607015e-34, 'c': 299792458}

# Input Definitions
GROUPS = [
    {'id': 'orbit', 'label': 'Orbit & Viewing', 'color': '#4a7dce', 'params': [
        {'k': 'lookAngle', 'label': 'Look Angle', 'unit': 'deg', 'min': 0, 'max': 45, 'step': 0.5, 'def': 20, 'decimals': 1},
        {'k': 'altitude', 'label': 'Orbit Altitude', 'unit': 'km', 'min': 300, 'max': 1200, 'step': 1, 'def': 617, 'decimals': 0},
        {'k': 'inclination', 'label': 'Inclination', 'unit': 'deg', 'min': 0, 'max': 180, 'step': 0.5, 'def': 98, 'decimals': 1},
        {'k': 'maxTilt', 'label': 'Max Tilt Angle', 'unit': 'deg', 'min': 0, 'max': 60, 'step': 0.5, 'def': 45, 'decimals': 1},
        {'k': 'minElev', 'label': 'Min Elevation', 'unit': 'deg', 'min': 5, 'max': 60, 'step': 0.5, 'def': 30, 'decimals': 1},
        {'k': 'ltan', 'label': 'LTAN', 'unit': 'hr', 'min': 0, 'max': 24, 'step': 0.1, 'def': 22.5, 'decimals': 1},
        {'k': 'dayOfYear', 'label': 'Day of Year', 'unit': 'day', 'min': 1, 'max': 365, 'step': 1, 'def': 172, 'decimals': 0},
        {'k': 'repeatCycle', 'label': 'Repeat Cycle', 'unit': 'days', 'min': 0.5, 'max': 16, 'step': 0.1, 'def': 4.5, 'decimals': 1},
    ]},
    {'id': 'optics', 'label': 'Sensor Optics', 'color': '#2e9e6a', 'params': [
        {'k': 'aperture', 'label': 'Aperture Dia.', 'unit': 'm', 'min': 0.1, 'max': 3, 'step': 0.01, 'def': 1.1, 'decimals': 2},
        {'k': 'focalLength', 'label': 'Focal Length', 'unit': 'm', 'min': 1, 'max': 30, 'step': 0.1, 'def': 13.3, 'decimals': 1},
        {'k': 'wavelengthRef', 'label': 'Wavelength (ref)', 'unit': 'nm', 'min': 300, 'max': 1000, 'step': 1, 'def': 625, 'decimals': 0},
        {'k': 'centralWavelength', 'label': 'Central Wavelength', 'unit': 'nm', 'min': 300, 'max': 1000, 'step': 1, 'def': 625, 'decimals': 0},
        {'k': 'bandwidth', 'label': 'Bandwidth', 'unit': 'nm', 'min': 10, 'max': 600, 'step': 1, 'def': 350, 'decimals': 0},
        {'k': 'numBands', 'label': 'Number of Bands', 'unit': '', 'min': 1, 'max': 60, 'step': 1, 'def': 29, 'decimals': 0},
    ]},
    {'id': 'integration', 'label': 'Sensor Integration', 'color': '#e2893d', 'params': [
        {'k': 'tdiStages', 'label': 'TDI Stages', 'unit': '', 'min': 1, 'max': 64, 'step': 1, 'def': 32, 'decimals': 0},
        {'k': 'opticalEfficiency', 'label': 'Optical Eff.', 'unit': '%', 'min': 40, 'max': 100, 'step': 1, 'def': 75, 'decimals': 0},
        {'k': 'numPixels', 'label': 'Pixels', 'unit': '', 'min': 1000, 'max': 60000, 'step': 100, 'def': 35000, 'decimals': 0},
    ]},
    {'id': 'radiometry', 'label': 'Sensor Radiometry', 'color': '#d94b61', 'params': [
        {'k': 'spectralRadiance', 'label': 'Spectral Radiance', 'unit': 'W/(m²sr·µm)', 'min': 5, 'max': 100, 'step': 1, 'def': 35, 'decimals': 0},
        {'k': 'QE', 'label': 'Quantum Eff.', 'unit': '%', 'min': 20, 'max': 95, 'step': 1, 'def': 70, 'decimals': 0},
        {'k': 'fullWell', 'label': 'Full Well Cap.', 'unit': 'e⁻', 'min': 10000, 'max': 120000, 'step': 500, 'def': 45000, 'decimals': 0},
        {'k': 'readNoise', 'label': 'Read Noise', 'unit': 'e⁻ rms', 'min': 1, 'max': 40, 'step': 0.5, 'def': 12, 'decimals': 1},
    ]},
    {'id': 'pixel', 'label': 'Pixel & Data Rate', 'color': '#8a5fcc', 'params': [
        {'k': 'pixelPitch', 'label': 'Pixel Pitch', 'unit': 'µm', 'min': 2, 'max': 20, 'step': 0.1, 'def': 6.7, 'decimals': 1},
        {'k': 'bitDepth', 'label': 'Bit Depth', 'unit': 'bits', 'min': 8, 'max': 16, 'step': 1, 'def': 11, 'decimals': 0},
    ]},
]

ALL_PARAMS = {p['k']: p for g in GROUPS for p in g['params']}

OUT_DEFS = [
    {'eng': 'spatial', 'k': 'IFOV', 'label': 'IFOV', 'unit': 'deg', 'mult': 180 / math.pi},
    {'eng': 'spatial', 'k': 'GSD', 'label': 'GSD', 'unit': 'm'},
    {'eng': 'spatial', 'k': 'diffRes', 'label': 'Diffraction-Limited Res.', 'unit': 'deg', 'mult': 180 / math.pi},
    {'eng': 'spatial', 'k': 'TFOV', 'label': 'Total FOV', 'unit': 'deg', 'mult': 180 / math.pi},
    {'eng': 'spatial', 'k': 'swathWidth', 'label': 'Swath Width', 'unit': 'km'},
    {'eng': 'spatial', 'k': 'fNumber', 'label': 'F-Number', 'unit': ''},
    {'eng': 'spatial', 'k': 'cutoffFreq', 'label': 'Cutoff Frequency', 'unit': 'cyc/m'},
    {'eng': 'spatial', 'k': 'nyquistFreq', 'label': 'Nyquist Frequency', 'unit': 'cyc/m'},
    {'eng': 'spatial', 'k': 'normFreq', 'label': 'Normalized Frequency', 'unit': ''},
    {'eng': 'spatial', 'k': 'mtfOptics', 'label': 'MTF Optics', 'unit': ''},
    {'eng': 'spatial', 'k': 'mtfSystem', 'label': 'MTF System', 'unit': ''},
    {'eng': 'spatial', 'k': 'gsdRatio', 'label': 'GSD Ratio', 'unit': ''},
    {'eng': 'spatial', 'k': 'motionBlur', 'label': 'Motion Blur', 'unit': 'm'},
    {'eng': 'spatial', 'k': 'blurPct', 'label': 'Blur %', 'unit': '%'},
    {'eng': 'spatial', 'k': 'solidAngle', 'label': 'Solid Angle', 'unit': 'sr'},
    {'eng': 'spatial', 'k': 'entranceApArea', 'label': 'Entrance Aperture Area', 'unit': 'm²'},
    {'eng': 'orbital', 'k': 'orbitalVel', 'label': 'Orbital Velocity', 'unit': 'km/s'},
    {'eng': 'orbital', 'k': 'groundTrackVel', 'label': 'Ground Track Velocity', 'unit': 'km/s'},
    {'eng': 'orbital', 'k': 'orbitPeriod', 'label': 'Orbit Period', 'unit': 'min'},
    {'eng': 'orbital', 'k': 'orbitsPerDay', 'label': 'Orbits per Day', 'unit': ''},
    {'eng': 'orbital', 'k': 'lineRate', 'label': 'Line Rate', 'unit': 'lines/s'},
    {'eng': 'orbital', 'k': 'integrationTime', 'label': 'Integration Time', 'unit': 's', 'sci': True},
    {'eng': 'orbital', 'k': 'FOR', 'label': 'Field of Regard', 'unit': 'km'},
    {'eng': 'orbital', 'k': 'groundWidthFOR', 'label': 'Ground Width of FOR', 'unit': 'km'},
    {'eng': 'orbital', 'k': 'nadirRevisit', 'label': 'Nadir Revisit Time', 'unit': 'days'},
    {'eng': 'orbital', 'k': 'actualRevisit', 'label': 'Actual Revisit Time', 'unit': 'days'},
    {'eng': 'orbital', 'k': 'earthCentralAngle', 'label': 'Earth Central Angle', 'unit': 'deg', 'mult': 180 / math.pi},
    {'eng': 'orbital', 'k': 'groundStationContact', 'label': 'Ground Station Contact', 'unit': 's'},
    {'eng': 'spectral', 'k': 'solarDeclSummer', 'label': 'Solar Declination (Summer)', 'unit': 'deg'},
    {'eng': 'spectral', 'k': 'solarDeclWinter', 'label': 'Solar Declination (Winter)', 'unit': 'deg'},
    {'eng': 'spectral', 'k': 'sunHourAngle', 'label': 'Sun-Orbit Hour Angle', 'unit': 'deg'},
    {'eng': 'spectral', 'k': 'betaSummer', 'label': 'Beta Angle (Summer)', 'unit': 'deg'},
    {'eng': 'spectral', 'k': 'betaWinter', 'label': 'Beta Angle (Winter)', 'unit': 'deg'},
    {'eng': 'radiometric', 'k': 'signal', 'label': 'Signal', 'unit': 'e⁻'},
    {'eng': 'radiometric', 'k': 'shotNoise', 'label': 'Shot Noise', 'unit': 'e⁻ rms'},
    {'eng': 'radiometric', 'k': 'snrSingle', 'label': 'SNR (single sample)', 'unit': ''},
    {'eng': 'radiometric', 'k': 'effectiveSignal', 'label': 'Effective Signal (TDI)', 'unit': 'e⁻'},
    {'eng': 'radiometric', 'k': 'finalSNR', 'label': 'Final SNR', 'unit': ''},
    {'eng': 'radiometric', 'k': 'totalDigitalLevels', 'label': 'Total Digital Levels', 'unit': 'levels'},
    {'eng': 'radiometric', 'k': 'dynamicRange', 'label': 'Dynamic Range', 'unit': 'dB'},
    {'eng': 'radiometric', 'k': 'rawDataRate', 'label': 'Raw Data Rate', 'unit': 'Mbps'},
]

ENGINES = [
    {"id": "spatial", "no": "01", "name": "Spatial Engine", "color": "#4dd8ff"},
    {"id": "orbital", "no": "02", "name": "Orbital / Temporal Engine", "color": "#5eeba0"},
    {"id": "spectral", "no": "03", "name": "Spectral Engine", "color": "#9b8cff"},
    {"id": "radiometric", "no": "04", "name": "Radiometric Engine", "color": "#ffb454"},
]

DEP = {
    'IFOV': ['pixelPitch', 'focalLength'],
    'GSD': ['altitude', 'lookAngle', 'pixelPitch', 'focalLength'],
    'diffRes': ['wavelengthRef', 'aperture'],
    'TFOV': ['numPixels', 'pixelPitch', 'focalLength'],
    'swathWidth': ['altitude', 'numPixels', 'pixelPitch', 'focalLength'],
    'fNumber': ['focalLength', 'aperture'],
    'cutoffFreq': ['aperture', 'wavelengthRef', 'focalLength'],
    'nyquistFreq': ['pixelPitch'],
    'normFreq': ['pixelPitch', 'aperture', 'wavelengthRef', 'focalLength'],
    'mtfOptics': ['pixelPitch', 'aperture', 'wavelengthRef', 'focalLength'],
    'mtfSystem': ['pixelPitch', 'aperture', 'wavelengthRef', 'focalLength'],
    'gsdRatio': ['altitude', 'numPixels', 'pixelPitch', 'focalLength', 'lookAngle'],
    'motionBlur': ['altitude', 'pixelPitch', 'focalLength', 'lookAngle'],
    'blurPct': ['altitude', 'pixelPitch', 'focalLength', 'lookAngle'],
    'pixelArea': ['pixelPitch'],
    'solidAngle': ['focalLength', 'aperture'],
    'entranceApArea': ['aperture'],
    'orbitalVel': ['altitude'],
    'groundTrackVel': ['altitude'],
    'orbitPeriod': ['altitude'],
    'orbitsPerDay': ['altitude'],
    'lineRate': ['altitude', 'pixelPitch', 'focalLength', 'lookAngle'],
    'integrationTime': ['altitude', 'pixelPitch', 'focalLength', 'lookAngle'],
    'FOR': ['altitude', 'numPixels', 'pixelPitch', 'focalLength', 'maxTilt'],
    'groundWidthFOR': ['altitude', 'lookAngle', 'numPixels', 'pixelPitch', 'focalLength'],
    'nadirRevisit': ['repeatCycle', 'altitude'],
    'actualRevisit': ['altitude', 'numPixels', 'pixelPitch', 'focalLength', 'maxTilt'],
    'earthCentralAngle': ['altitude', 'minElev'],
    'groundStationContact': ['altitude', 'minElev'],
    'solarDeclSummer': ['dayOfYear'],
    'solarDeclWinter': ['dayOfYear'],
    'sunHourAngle': ['ltan'],
    'betaSummer': ['dayOfYear', 'inclination', 'ltan'],
    'betaWinter': ['dayOfYear', 'inclination', 'ltan'],
    'photonEnergy': ['centralWavelength'],
    'pixelPower': ['spectralRadiance', 'bandwidth', 'pixelPitch', 'focalLength', 'aperture', 'opticalEfficiency'],
    'signal': ['spectralRadiance', 'bandwidth', 'pixelPitch', 'focalLength', 'aperture', 'opticalEfficiency', 'altitude', 'lookAngle', 'QE', 'centralWavelength'],
    'shotNoise': ['spectralRadiance', 'bandwidth', 'pixelPitch', 'focalLength', 'aperture', 'opticalEfficiency', 'altitude', 'lookAngle', 'QE', 'centralWavelength'],
    'snrSingle': ['spectralRadiance', 'bandwidth', 'pixelPitch', 'focalLength', 'aperture', 'opticalEfficiency', 'altitude', 'lookAngle', 'QE', 'centralWavelength'],
    'effectiveSignal': ['spectralRadiance', 'bandwidth', 'pixelPitch', 'focalLength', 'aperture', 'opticalEfficiency', 'altitude', 'lookAngle', 'QE', 'centralWavelength', 'tdiStages'],
    'finalSNR': ['spectralRadiance', 'bandwidth', 'pixelPitch', 'focalLength', 'aperture', 'opticalEfficiency', 'altitude', 'lookAngle', 'QE', 'centralWavelength', 'tdiStages', 'readNoise'],
    'totalDigitalLevels': ['bitDepth'],
    'dynamicRange': ['fullWell', 'readNoise'],
    'rawDataRate': ['numPixels', 'bitDepth', 'altitude', 'pixelPitch', 'focalLength', 'lookAngle', 'numBands'],
}

def default_inputs():
    return {p['k']: p['def'] for g in GROUPS for p in g['params']}

def compute_all(P):
    O = {}
    rad = lambda d: d * math.pi / 180.0
    deg = lambda r: r * 180.0 / math.pi
    
    # SPATIAL
    O['IFOV'] = (P['pixelPitch'] / 1e6) / P['focalLength']
    O['GSD'] = (P['altitude'] * 1000) * O['IFOV'] / math.cos(rad(P['lookAngle']))
    O['diffRes'] = 1.22 * (P['wavelengthRef'] / 1e9) / P['aperture']
    O['TFOV'] = P['numPixels'] * O['IFOV']
    O['swathWidth'] = 2 * P['altitude'] * math.tan(O['TFOV'] / 2)
    O['fNumber'] = P['focalLength'] / P['aperture']
    O['cutoffFreq'] = P['aperture'] / ((P['wavelengthRef'] / 1e9) * P['focalLength'])
    O['nyquistFreq'] = 1 / (2 * (P['pixelPitch'] / 1e6))
    O['normFreq'] = O['nyquistFreq'] / O['cutoffFreq']
    O['mtfDetector'] = 2 / math.pi
    nf = min(O['normFreq'], 0.999999)
    O['mtfOptics'] = (2 / math.pi) * (math.acos(nf) - nf * math.sqrt(1 - nf * nf))
    O['mtfSystem'] = O['mtfDetector'] * O['mtfOptics']
    O['gsdRatio'] = O['swathWidth'] / O['GSD']
    
    # ORBITAL
    O['orbitalVel'] = math.sqrt(CONST['mu'] / (CONST['Re'] + P['altitude']))
    O['groundTrackVel'] = O['orbitalVel'] * (CONST['Re'] / (CONST['Re'] + P['altitude']))
    O['orbitPeriod'] = ((2 * math.pi * (CONST['Re'] + P['altitude'])) / O['orbitalVel']) / 60
    O['orbitsPerDay'] = 1440 / O['orbitPeriod']
    O['lineRate'] = (O['groundTrackVel'] * 1000) / O['GSD']
    O['integrationTime'] = O['GSD'] / (O['groundTrackVel'] * 1000)
    O['motionBlur'] = (O['groundTrackVel'] * 1000) * O['integrationTime']
    O['blurPct'] = (O['motionBlur'] / O['GSD']) * 100
    O['pixelArea'] = math.pow(P['pixelPitch'] / 1e6, 2)
    O['solidAngle'] = math.pi / (4 * O['fNumber'] * O['fNumber'])
    O['entranceApArea'] = math.pi * P['aperture'] * P['aperture'] / 4
    
    O['FOR'] = O['swathWidth'] + 2 * P['altitude'] * math.tan(rad(P['maxTilt']))
    O['groundWidthFOR'] = 2 * P['altitude'] * math.tan(rad(P['lookAngle']) + O['TFOV'] / 2)
    O['nadirRevisit'] = P['repeatCycle'] / O['orbitsPerDay']
    O['actualRevisit'] = (2 * math.pi * CONST['Re']) / (O['FOR'] * O['orbitsPerDay'])
    O['earthCentralAngle'] = math.acos((CONST['Re'] / (CONST['Re'] + P['altitude'])) * math.cos(rad(P['minElev']))) - rad(P['minElev'])
    O['groundStationContact'] = O['orbitPeriod'] * 60 * (2 * O['earthCentralAngle']) / (2 * math.pi)
    
    # SPECTRAL
    O['solarDeclSummer'] = 23.44 * math.sin(rad((360 / 365) * (P['dayOfYear'] + 284)))
    O['solarDeclWinter'] = -23.44 * math.sin(rad((360 / 365) * (P['dayOfYear'] + 284)))
    O['sunHourAngle'] = 15 * (P['ltan'] - 12)
    O['betaSummer'] = deg(math.asin(math.cos(rad(O['solarDeclSummer'])) * math.sin(rad(P['inclination'])) * math.sin(rad(O['sunHourAngle'])) + math.sin(rad(O['solarDeclSummer'])) * math.cos(rad(P['inclination']))))
    O['betaWinter'] = deg(math.asin(math.cos(rad(O['solarDeclWinter'])) * math.sin(rad(P['inclination'])) * math.sin(rad(O['sunHourAngle'])) + math.sin(rad(O['solarDeclWinter'])) * math.cos(rad(P['inclination']))))
    
    # RADIOMETRIC
    O['photonEnergy'] = (CONST['h'] * CONST['c']) / (P['centralWavelength'] / 1e9)
    O['pixelPower'] = P['spectralRadiance'] * (P['bandwidth'] / 1000) * O['pixelArea'] * O['solidAngle'] * (P['opticalEfficiency'] / 100)
    O['signal'] = (O['pixelPower'] * O['integrationTime'] * (P['QE'] / 100)) / O['photonEnergy']
    O['shotNoise'] = math.sqrt(max(O['signal'], 0))
    O['snrSingle'] = O['signal'] / O['shotNoise'] if O['shotNoise'] > 0 else 0
    O['effectiveSignal'] = O['signal'] * P['tdiStages']
    O['finalSNR'] = O['effectiveSignal'] / math.sqrt(O['effectiveSignal'] + P['readNoise'] * P['readNoise']) if (O['effectiveSignal'] + P['readNoise'] * P['readNoise']) > 0 else 0
    O['totalDigitalLevels'] = math.pow(2, P['bitDepth'])
    O['dynamicRange'] = 20 * math.log10(P['fullWell'] / P['readNoise']) if P['readNoise'] > 0 else 0
    O['rawDataRate'] = (P['numPixels'] * P['bitDepth'] * O['lineRate'] * P['numBands']) / 1e6
    return O

def fmt(v, sci=False):
    if not math.isfinite(v): return "—"
    if sci: return f"{v:.2e}"
    if abs(v) >= 1000: return f"{v:.1f}"
    if abs(v) < 0.01 and v != 0: return f"{v:.2e}"
    return f"{v:.3f}".rstrip('0').rstrip('.')

def efficiency(O):
    clamp01 = lambda x: max(0, min(1, x))
    spatial = clamp01(1 - (O['GSD'] - 0.15) / (3.0 - 0.15))
    radiometric = clamp01((O['finalSNR'] - 5) / (150 - 5))
    temporal = clamp01(1 - (O['actualRevisit'] - 0.3) / (10 - 0.3))
    dynamic = clamp01((O['dynamicRange'] - 30) / (85 - 30))
    overall = (spatial * 0.3 + radiometric * 0.3 + temporal * 0.2 + dynamic * 0.2) * 100
    return {'overall': overall, 'spatial': spatial*100, 'radiometric': radiometric*100, 'temporal': temporal*100, 'dynamic': dynamic*100}

def node_label(key):
    for d in OUT_DEFS:
        if d['k'] == key: return d['label']
    return ALL_PARAMS.get(key, {}).get('label', key)

def engine_of(key):
    for d in OUT_DEFS:
        if d['k'] == key: return d['eng']
    return None

def dependency_edges_for_engine(eng_id):
    in_keys = set()
    edges = set()
    out_keys = []
    
    for out in OUT_DEFS:
        if out['eng'] != eng_id: continue
        out_keys.append(out['k'])
        deps = DEP.get(out['k'], [])
        for d in deps:
            edges.add((d, out['k']))
            in_keys.add(d)
    
    return sorted(list(in_keys)), out_keys, sorted(list(edges))