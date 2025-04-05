#!/usr/bin/env python3
"""
Fix script for AssetAPI to add the missing _calculate_basic_scores method.
"""
import os
import sys
from pathlib import Path

def main():
    # Path to the asset_api.py file
    asset_api_path = Path(__file__).parent / "asset_api.py"
    
    if not asset_api_path.exists():
        print(f"Error: {asset_api_path} does not exist")
        sys.exit(1)
    
    # Read the file content
    with open(asset_api_path, "r") as f:
        content = f.read()
    
    # Check if the _calculate_basic_scores method already exists
    if "_calculate_basic_scores" in content:
        print("The _calculate_basic_scores method already exists")
        return
    
    # Find the position to insert the method (after the _create_response method)
    method_position = content.find("def _to_camel_case")
    
    if method_position == -1:
        print("Could not find the appropriate position to insert the method")
        sys.exit(1)
    
    # Define the _calculate_basic_scores method
    calculate_scores_method = '''    
    def _calculate_basic_scores(self, asset: dict) -> dict:
        """Рассчитывает базовые скоры для актива."""
        try:
            scores = {}
            
            # Технические скоры
            if 'momentum3m' in asset and asset['momentum3m'] is not None:
                scores['momentum_score'] = min(max(asset['momentum3m'] / 0.3, -1.0), 1.0)
            else:
                scores['momentum_score'] = 0.0
                
            if 'volatility3m' in asset and asset['volatility3m'] is not None:
                # Низкая волатильность - хорошо, высокая - плохо
                vol_normalized = min(asset['volatility3m'] / 0.5, 1.0)
                scores['volatility_score'] = 1.0 - vol_normalized
            else:
                scores['volatility_score'] = 0.0
            
            # Суммарный скор
            total_score = 0.0
            weights = {
                'momentum_score': 0.7,
                'volatility_score': 0.3
            }
            
            for key, weight in weights.items():
                if key in scores:
                    total_score += scores[key] * weight
            
            scores['total_score'] = total_score
            return scores
        except Exception as e:
            from logging import getLogger
            logger = getLogger(__name__)
            logger.error(f"Error calculating scores: {str(e)}")
            return {
                'momentum_score': 0.0,
                'volatility_score': 0.0,
                'total_score': 0.0
            }
'''
    
    # Insert the method before _to_camel_case
    new_content = content[:method_position] + calculate_scores_method + content[method_position:]
    
    # Backup the original file
    backup_path = asset_api_path.with_suffix(".py.bak")
    with open(backup_path, "w") as f:
        f.write(content)
    
    # Write the new content
    with open(asset_api_path, "w") as f:
        f.write(new_content)
    
    print(f"Successfully added the _calculate_basic_scores method to {asset_api_path}")
    print(f"Original file backed up to {backup_path}")

if __name__ == "__main__":
    main() 