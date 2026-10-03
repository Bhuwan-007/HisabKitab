from . import missing, tax_rate, tax_type, duplicates, cutoff

def run_all_tax_rules(dataset, matches, cfg):
    findings = []
    findings.extend(missing.run(dataset, matches, cfg))
    findings.extend(tax_rate.run(dataset, matches, cfg))
    findings.extend(tax_type.run(dataset, matches, cfg))
    findings.extend(duplicates.run(dataset, matches, cfg))
    findings.extend(cutoff.run(dataset, matches, cfg))
    return findings
