#!/usr/bin/env python3
"""
Evaluation Runner & Metrics Suite
HackerRank Orchestrate October 2026 - Ghost Data Still Exists

Computes:
1. Case-level deletion status accuracy
2. Row-level accuracy
3. Field-level accuracy (step_no, phase, system_id, resource_id, operation, state, evidence_id)
4. Sequence accuracy
5. Custom test cases evaluation
"""

import os
import sys
import json
import csv

# Add parent dir to path to import DeletionAuditAgent
cur_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(cur_dir, '..'))
sys.path.insert(0, parent_dir)
from main import DeletionAuditAgent, sort_steps, resolve_paths

def evaluate_samples():
    repo_root, dataset_dir, _ = resolve_paths()
    print("=" * 60)
    print("NORTHSTAR SHOP DELETION AUDIT - EVALUATION SUITE")
    print("=" * 60)
    
    agent = DeletionAuditAgent(dataset_dir)
    agent.load_identities()
    agent.load_evidence_manifest()
    agent.index_system_activity()
    agent.extract_evidence()
    
    sample_req_path = os.path.join(dataset_dir, 'sample_deletion_requests.csv')
    sample_out_path = os.path.join(dataset_dir, 'sample_output.csv')
    
    golden = {}
    with open(sample_out_path, 'r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        for r in reader:
            golden[r['case_id']] = {
                'deletion_status': r['deletion_status'],
                'steps': json.loads(r['steps_json'])
            }
            
    total_cases = len(golden)
    correct_status_cases = 0
    perfect_step_cases = 0
    total_steps_golden = 0
    matched_steps = 0
    total_fields = 0
    matched_fields = 0
    sequence_matches = 0
    
    with open(sample_req_path, 'r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            cid = row['case_id']
            if cid not in golden:
                continue
            pred_status, pred_steps = agent.audit_case(
                cid, row['email'], row['requested_at'], row['reported_status'],
                row['reported_at'], row['audit_at'], row.get('request_text', '')
            )
            gold = golden[cid]
            gold_status = gold['deletion_status']
            gold_steps = gold['steps']
            
            # Status accuracy
            if pred_status == gold_status:
                correct_status_cases += 1
                
            # Sequence accuracy
            pred_ops = [(s['phase'], s['operation']) for s in pred_steps]
            gold_ops = [(s['phase'], s['operation']) for s in gold_steps]
            if pred_ops == gold_ops:
                sequence_matches += 1
                
            # Step & field level comparison
            is_case_perfect = (pred_status == gold_status and len(pred_steps) == len(gold_steps))
            total_steps_golden += len(gold_steps)
            
            min_len = min(len(pred_steps), len(gold_steps))
            for i in range(min_len):
                ps = pred_steps[i]
                gs = gold_steps[i]
                step_fields_match = True
                for fld in ['step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id']:
                    total_fields += 1
                    if ps.get(fld) == gs.get(fld):
                        matched_fields += 1
                    else:
                        step_fields_match = False
                if step_fields_match:
                    matched_steps += 1
                else:
                    is_case_perfect = False
                    
            if len(pred_steps) != len(gold_steps):
                is_case_perfect = False
                total_fields += abs(len(pred_steps) - len(gold_steps)) * 7
                
            if is_case_perfect:
                perfect_step_cases += 1

    print("\n--- Evaluation Results Across 32 Benchmark Requests ---")
    print(f"Case-Level Status Accuracy:  {correct_status_cases}/{total_cases} ({correct_status_cases/total_cases*100:.2f}%)")
    print(f"Perfect Case Sequence Match: {sequence_matches}/{total_cases} ({sequence_matches/total_cases*100:.2f}%)")
    print(f"Step-Level Exact Match:      {matched_steps}/{total_steps_golden} ({matched_steps/total_steps_golden*100:.2f}%)")
    print(f"Field-Level Exact Match:     {matched_fields}/{total_fields} ({matched_fields/total_fields*100:.2f}%)")
    print(f"Overall End-to-End Accuracy: {perfect_step_cases}/{total_cases} ({perfect_step_cases/total_cases*100:.2f}%)")
    print("=" * 60)

if __name__ == '__main__':
    evaluate_samples()
