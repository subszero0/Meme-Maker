#!/usr/bin/env python3

def analyze_instagram_urls():
    """Analyze differences between working and failing Instagram URLs"""
    
    working_id = 'DLjuZlDTrq3'
    failing_id = 'DLiGaJABO_a'
    
    print('🔍 Instagram URL Structure Analysis')
    print('=' * 50)
    print(f'Working ID: {working_id} (length: {len(working_id)})')
    print(f'Failing ID: {failing_id} (length: {len(failing_id)})')
    print()
    
    # Character analysis
    print('📝 Character Analysis:')
    print(f'Working has underscore: {"_" in working_id}')
    print(f'Failing has underscore: {"_" in failing_id}')
    print(f'Working has uppercase: {any(c.isupper() for c in working_id)}')
    print(f'Failing has uppercase: {any(c.isupper() for c in failing_id)}')
    print()
    
    # Length difference
    if len(working_id) != len(failing_id):
        print(f'⚠️  Length difference: {abs(len(working_id) - len(failing_id))} characters')
    else:
        print('✅ Same length')
    print()
    
    # Character set analysis
    working_chars = set(working_id)
    failing_chars = set(failing_id)
    
    print('🔤 Character Set Analysis:')
    print(f'Working characters: {sorted(working_chars)}')
    print(f'Failing characters: {sorted(failing_chars)}')
    print(f'Common characters: {sorted(working_chars & failing_chars)}')
    print(f'Working unique: {sorted(working_chars - failing_chars)}')
    print(f'Failing unique: {sorted(failing_chars - working_chars)}')
    print()
    
    # Potential root causes
    print('🔍 Potential Root Causes:')
    print('1. Content-specific Instagram restrictions')
    print('2. Cache key generation issues with underscores')
    print('3. URL encoding differences in production')
    print('4. Specific content being geo-blocked or restricted')
    print('5. Instagram rate limiting based on content patterns')
    print('6. Backend regex/parsing issues with certain character patterns')
    print()
    
    # Hypothesis
    print('💡 Leading Hypothesis:')
    if '_' in failing_id and '_' not in working_id:
        print('The failing URL contains an underscore (_) while working does not.')
        print('This could cause:')
        print('- URL encoding issues in production environment')
        print('- Backend string parsing problems')
        print('- Cache key generation conflicts')
        print('- Instagram API differences based on ID format')
    else:
        print('Character pattern is not obviously different.')
        print('This suggests content-specific restrictions or caching issues.')

if __name__ == '__main__':
    analyze_instagram_urls() 