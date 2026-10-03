from . import missing, tax_rate, tax_type, duplicates, cutoff

def run_all_tax_rules(dataset, matches, cfg):
    findings = []
    findings.extend(missing.run(dataset, matches, cfg))
    findings.extend(tax_rate.run(dataset, matches, cfg))
    findings.extend(tax_type.run(dataset, matches, cfg))
    findings.extend(duplicates.run(dataset, matches, cfg))
    findings.extend(cutoff.run(dataset, matches, cfg))
    return findings

def run_all_payment_rules(dataset, matches, cfg):
    from . import payment_clock, upi_mdr, payments
    findings = []
    findings.extend(payment_clock.run(dataset, matches, cfg))
    findings.extend(upi_mdr.run(dataset, matches, cfg))
    findings.extend(payments.run(dataset, matches, cfg))
    return findings
