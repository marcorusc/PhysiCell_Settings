#!/usr/bin/env python3
"""
Test script to validate that all three configurations can be reproduced correctly.
"""

import sys
import os
import xml.etree.ElementTree as ET

def compare_xml_elements(elem1, elem2, path=""):
    """Compare two XML elements and their children."""
    differences = []
    
    # Compare tag names
    if elem1.tag != elem2.tag:
        differences.append(f"{path}: Tag mismatch: {elem1.tag} != {elem2.tag}")
    
    # Compare text content (ignore whitespace)
    text1 = (elem1.text or "").strip()
    text2 = (elem2.text or "").strip()
    if text1 != text2:
        differences.append(f"{path}/{elem1.tag}: Text mismatch: '{text1}' != '{text2}'")
    
    # Compare attributes
    attrs1 = dict(elem1.attrib)
    attrs2 = dict(elem2.attrib)
    
    for attr in set(attrs1.keys()) | set(attrs2.keys()):
        if attr not in attrs1:
            differences.append(f"{path}/{elem1.tag}@{attr}: Missing in generated")
        elif attr not in attrs2:
            differences.append(f"{path}/{elem1.tag}@{attr}: Extra in generated")
        elif attrs1[attr] != attrs2[attr]:
            differences.append(f"{path}/{elem1.tag}@{attr}: '{attrs1[attr]}' != '{attrs2[attr]}'")
    
    # Compare children
    children1 = list(elem1)
    children2 = list(elem2)
    
    # Create mappings by tag for comparison
    children1_by_tag = {}
    for child in children1:
        tag = child.tag
        if tag not in children1_by_tag:
            children1_by_tag[tag] = []
        children1_by_tag[tag].append(child)
    
    children2_by_tag = {}
    for child in children2:
        tag = child.tag
        if tag not in children2_by_tag:
            children2_by_tag[tag] = []
        children2_by_tag[tag].append(child)
    
    # Compare children by tag
    all_tags = set(children1_by_tag.keys()) | set(children2_by_tag.keys())
    for tag in all_tags:
        list1 = children1_by_tag.get(tag, [])
        list2 = children2_by_tag.get(tag, [])
        
        if len(list1) != len(list2):
            differences.append(f"{path}/{elem1.tag}: Child count mismatch for {tag}: {len(list1)} != {len(list2)}")
        
        # Compare corresponding children
        for i in range(min(len(list1), len(list2))):
            child_path = f"{path}/{elem1.tag}"
            differences.extend(compare_xml_elements(list1[i], list2[i], child_path))
    
    return differences

def validate_xml_structure(generated_file, target_file, config_name):
    """Validate the generated XML against target XML."""
    print(f"\n=== Validating {config_name} ===")
    
    try:
        # Parse both XMLs
        generated_tree = ET.parse(generated_file)
        target_tree = ET.parse(target_file)
        
        generated_root = generated_tree.getroot()
        target_root = target_tree.getroot()
        
        # Compare structure
        differences = compare_xml_elements(generated_root, target_root)
        
        if not differences:
            print(f"✅ {config_name}: Perfect match!")
            return True
        else:
            print(f"⚠️  {config_name}: Found {len(differences)} differences:")
            for diff in differences[:10]:  # Show first 10 differences
                print(f"   {diff}")
            if len(differences) > 10:
                print(f"   ... and {len(differences) - 10} more differences")
            return False
            
    except Exception as e:
        print(f"❌ {config_name}: Error during validation: {e}")
        return False

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
