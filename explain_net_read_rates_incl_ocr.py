#!/usr/bin/env python3
"""
Comprehensive explanation of Net read rates including OCR calculation
"""

def explain_net_read_rates_incl_ocr():
    """Explain how Net read rates including OCR are calculated"""
    
    print("=== NET READ RATES INCLUDING OCR CALCULATION ===")
    print()
    
    print("The Net read rates including OCR calculation involves several steps:")
    print()
    
    print("STEP 1: Calculate base values")
    print("─" * 50)
    print("• total_entered = Total number of images entered")
    print("• actual_sessions = Total number of sessions")  
    print("• sessions_read_failure = Number of sessions classified as 'read failure'")
    print("• sessions_false_noread = Number of sessions with False NoRead flag")
    print("• sessions_ocr_readable = Number of sessions with at least one OCR readable image")
    print("• sessions_ocr_readable_non_failure = OCR readable sessions that are NOT 'read failure'")
    print()
    
    print("STEP 2: Calculate totals for OCR inclusion")
    print("─" * 50)
    print("• total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure")
    print("• total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure")
    print()
    
    print("STEP 3: Calculate successful reads (excluding OCR)")
    print("─" * 50)
    print("• successful_reads_excl_ocr = total_readable_excl_ocr - sessions_read_failure + sessions_false_noread")
    print("• net_numerator_excl_ocr = successful_reads_excl_ocr")
    print()
    
    print("STEP 4: Calculate successful reads (including OCR)")
    print("─" * 50)
    print("• sessions_read_using_ocr = sessions_ocr_readable (all OCR readable sessions)")
    print("• net_numerator_incl_ocr = net_numerator_excl_ocr + sessions_read_using_ocr")
    print()
    
    print("STEP 5: Calculate final rate")
    print("─" * 50)
    print("• Net read rate incl. OCR = (net_numerator_incl_ocr / total_readable_incl_ocr) × 100")
    print()
    
    print("=== COMPLETE FORMULA BREAKDOWN ===")
    print()
    print("Net read rate incl. OCR = ((successful_reads_excl_ocr + sessions_read_using_ocr) / total_readable_incl_ocr) × 100")
    print()
    print("Where:")
    print("• successful_reads_excl_ocr = (total_entered - actual_sessions + sessions_read_failure) - sessions_read_failure + sessions_false_noread")
    print("• sessions_read_using_ocr = sessions with at least one OCR readable image")
    print("• total_readable_incl_ocr = (total_entered - actual_sessions + sessions_read_failure) + sessions_ocr_readable_non_failure")
    print()
    
    print("=== SIMPLIFIED FORMULA ===")
    print()
    print("Net read rate incl. OCR = ((total_entered - actual_sessions + sessions_false_noread + sessions_ocr_readable) / (total_entered - actual_sessions + sessions_read_failure + sessions_ocr_readable_non_failure)) × 100")
    print()
    
    print("=== EXAMPLE CALCULATION ===")
    print()
    
    # Example values
    total_entered = 10
    actual_sessions = 8
    sessions_read_failure = 3
    sessions_false_noread = 1
    sessions_ocr_readable = 2
    sessions_ocr_readable_non_failure = 1
    
    print("Example data:")
    print(f"• total_entered = {total_entered}")
    print(f"• actual_sessions = {actual_sessions}")
    print(f"• sessions_read_failure = {sessions_read_failure}")
    print(f"• sessions_false_noread = {sessions_false_noread}")
    print(f"• sessions_ocr_readable = {sessions_ocr_readable}")
    print(f"• sessions_ocr_readable_non_failure = {sessions_ocr_readable_non_failure}")
    print()
    
    # Step-by-step calculation
    total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure
    total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure
    successful_reads_excl_ocr = total_readable_excl_ocr - sessions_read_failure + sessions_false_noread
    net_numerator_incl_ocr = successful_reads_excl_ocr + sessions_ocr_readable
    rate_incl_ocr = (net_numerator_incl_ocr / total_readable_incl_ocr) * 100
    
    print("Step-by-step calculation:")
    print(f"1. total_readable_excl_ocr = {total_entered} - {actual_sessions} + {sessions_read_failure} = {total_readable_excl_ocr}")
    print(f"2. total_readable_incl_ocr = {total_readable_excl_ocr} + {sessions_ocr_readable_non_failure} = {total_readable_incl_ocr}")
    print(f"3. successful_reads_excl_ocr = {total_readable_excl_ocr} - {sessions_read_failure} + {sessions_false_noread} = {successful_reads_excl_ocr}")
    print(f"4. net_numerator_incl_ocr = {successful_reads_excl_ocr} + {sessions_ocr_readable} = {net_numerator_incl_ocr}")
    print(f"5. Net read rate incl. OCR = ({net_numerator_incl_ocr} / {total_readable_incl_ocr}) × 100 = {rate_incl_ocr:.2f}%")
    print()
    
    print("=== KEY CONCEPTS ===")
    print()
    print("• OCR readable sessions are added to BOTH numerator and denominator")
    print("• False NoRead sessions improve the success rate by correcting misclassifications")
    print("• OCR readable non-failure sessions expand the total readable pool")
    print("• All OCR readable sessions (regardless of classification) count as successful reads")
    print()
    
    print("=== DIFFERENCE FROM EXCL. OCR ===")
    print()
    rate_excl_ocr = (successful_reads_excl_ocr / total_readable_excl_ocr) * 100
    improvement = rate_incl_ocr - rate_excl_ocr
    print(f"• Net read rate excl. OCR = {rate_excl_ocr:.2f}%")
    print(f"• Net read rate incl. OCR = {rate_incl_ocr:.2f}%")
    print(f"• OCR improvement = {improvement:+.2f} percentage points")

if __name__ == "__main__":
    explain_net_read_rates_incl_ocr()