#!/usr/bin/env python3
"""
Test script to validate that all three configurations can be reproduced correctly.
"""

import sys
import os
import xml.etree.ElementTree as ET
import difflib

def compare_xml_elements_strict(elem1, elem2, path=""):
    """Compare two XML elements and their children strictly (order and whitespace matters)."""
    differences = []
    
    # Compare tag names
    if elem1.tag != elem2.tag:
        differences.append(f"{path}: Tag mismatch: {elem1.tag} != {elem2.tag}")
        return differences # Cannot compare further if tags differ
    
    # Compare text content (strict, no stripping)
    text1 = elem1.text or ""
    text2 = elem2.text or ""
    if text1 != text2:
        # Try to be helpful: if they differ only by whitespace, say so
        if text1.strip() == text2.strip():
             differences.append(f"{path}/{elem1.tag}: Text whitespace mismatch: '{repr(text1)}' != '{repr(text2)}'")
        else:
             differences.append(f"{path}/{elem1.tag}: Text mismatch: '{text1}' != '{text2}'")

    # Compare tail content (whitespace after tag)
    tail1 = elem1.tail or ""
    tail2 = elem2.tail or ""
    if tail1 != tail2:
         if tail1.strip() == tail2.strip():
             differences.append(f"{path}/{elem1.tag}: Tail whitespace mismatch: '{repr(tail1)}' != '{repr(tail2)}'")
         else:
             differences.append(f"{path}/{elem1.tag}: Tail mismatch: '{tail1}' != '{tail2}'")
    
    # Compare attributes
    attrs1 = dict(elem1.attrib)
    attrs2 = dict(elem2.attrib)
    
    if attrs1 != attrs2:
        for attr in set(attrs1.keys()) | set(attrs2.keys()):
            if attr not in attrs1:
                differences.append(f"{path}/{elem1.tag}@{attr}: Missing in generated")
            elif attr not in attrs2:
                differences.append(f"{path}/{elem1.tag}@{attr}: Extra in generated")
            elif attrs1[attr] != attrs2[attr]:
                differences.append(f"{path}/{elem1.tag}@{attr}: '{attrs1[attr]}' != '{attrs2[attr]}'")
    
    # Compare children strictly by index
    children1 = list(elem1)
    children2 = list(elem2)
    
    if len(children1) != len(children2):
        differences.append(f"{path}/{elem1.tag}: Child count mismatch: {len(children1)} != {len(children2)}")
    
    # Compare corresponding children
    for i in range(min(len(children1), len(children2))):
        child_path = f"{path}/{elem1.tag}[{i}]"
        differences.extend(compare_xml_elements_strict(children1[i], children2[i], child_path))
    
    return differences

def validate_file_content(generated_file, target_file, config_name):
    """Validate that files are textually identical."""
    print(f"   Checking file content identity for {config_name}...")
    try:
        with open(generated_file, 'r') as f1, open(target_file, 'r') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
            
        diff = list(difflib.unified_diff(
            lines1, lines2, 
            fromfile=f"Generated ({generated_file})", 
            tofile=f"Target ({target_file})",
            lineterm=''
        ))
        
        if not diff:
            print(f"   ✅ Content matches exactly!")
            return True
        else:
            print(f"   ❌ Content mismatch! ({len(diff)} diff lines)")
            # Print first few diffs
            for line in diff[:10]:
                print(f"      {line.rstrip()}")
            if len(diff) > 10:
                print(f"      ... and {len(diff) - 10} more lines")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading files: {e}")
        return False

def validate_xml_structure(generated_file, target_file, config_name):
    """Validate the generated XML against target XML."""
    print(f"\n=== Validating {config_name} ===")
    
    structure_match = False
    content_match = False
    
    try:
        # Parse both XMLs
        generated_tree = ET.parse(generated_file)
        target_tree = ET.parse(target_file)
        
        generated_root = generated_tree.getroot()
        target_root = target_tree.getroot()
        
        # Compare structure
        differences = compare_xml_elements_strict(generated_root, target_root)
        
        if not differences:
            print(f"   ✅ XML Structure matches exactly (including whitespace/order)!")
            structure_match = True
        else:
            print(f"   ⚠️  XML Structure mismatch ({len(differences)} differences):")
            for diff in differences[:10]:  # Show first 10 differences
                print(f"      {diff}")
            if len(differences) > 10:
                print(f"      ... and {len(differences) - 10} more differences")
            structure_match = False
            
    except Exception as e:
        print(f"   ❌ Error during XML parsing: {e}")
        structure_match = False

    # Check exact file content
    content_match = validate_file_content(generated_file, target_file, config_name)
    
    return structure_match and content_match

def main():
    """Run validation tests."""
    print("PhysiCell Configuration Package Validation")
    print("=" * 50)
    
    # Generate all configurations
    print("Generating configurations...")
    
    os.system("python3 examples/generate_basic.py")
    os.system("python3 examples/generate_rules.py") 
    os.system("python3 examples/generate_foxp3.py")
    
    # Validate configurations
    validation_results = []
    
    configs = [
        ("test_output/generated_basic.xml", "examples/PhysiCell_settings.xml", "Basic Template"),
        ("test_output/generated_rules.xml", "examples/PhysiCell_settings_rules.xml", "Cell Rules"),
        ("test_output/generated_foxp3.xml", "examples/PhysiCell_settings_FOXP3_2_mutant.xml", "PhysiBoSS FOXP3"),
    ]
    
    for generated, target, name in configs:
        if os.path.exists(generated) and os.path.exists(target):
            result = validate_xml_structure(generated, target, name)
            validation_results.append((name, result))
        else:
            print(f"❌ {name}: Missing files - Generated: {os.path.exists(generated)}, Target: {os.path.exists(target)}")
            validation_results.append((name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("VALIDATION SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for _, result in validation_results if result)
    total = len(validation_results)
    
    for name, result in validation_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOverall: {passed}/{total} configurations validated successfully")
    
    if passed == total:
        print("🎉 All configurations are correctly reproduced!")
    else:
        print("⚠️  Some configurations need refinement")

if __name__ == "__main__":
    main()
