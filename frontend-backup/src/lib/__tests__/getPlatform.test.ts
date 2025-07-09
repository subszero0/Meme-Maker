import getPlatform, { Platform } from '../getPlatform';

describe('getPlatform', () => {
  describe('YouTube detection', () => {
    it('detects youtube.com URLs', () => {
      expect(getPlatform('https://youtube.com/watch?v=test')).toBe('youtube');
      expect(getPlatform('http://youtube.com/watch?v=test')).toBe('youtube');
      expect(getPlatform('https://www.youtube.com/watch?v=test')).toBe('youtube');
    });

    it('detects youtu.be URLs', () => {
      expect(getPlatform('https://youtu.be/test123')).toBe('youtube');
      expect(getPlatform('http://youtu.be/test123')).toBe('youtube');
    });

    it('detects m.youtube.com URLs', () => {
      expect(getPlatform('https://m.youtube.com/watch?v=test')).toBe('youtube');
      expect(getPlatform('http://m.youtube.com/watch?v=test')).toBe('youtube');
    });
  });

  describe('Instagram detection', () => {
    it('detects instagram.com URLs', () => {
      expect(getPlatform('https://instagram.com/p/test')).toBe('instagram');
      expect(getPlatform('http://instagram.com/p/test')).toBe('instagram');
      expect(getPlatform('https://www.instagram.com/p/test')).toBe('instagram');
    });
  });

  describe('Facebook detection', () => {
    it('detects facebook.com URLs', () => {
      expect(getPlatform('https://facebook.com/video/test')).toBe('facebook');
      expect(getPlatform('http://facebook.com/video/test')).toBe('facebook');
      expect(getPlatform('https://www.facebook.com/video/test')).toBe('facebook');
    });

    it('detects fb.watch URLs', () => {
      expect(getPlatform('https://fb.watch/test123')).toBe('facebook');
      expect(getPlatform('http://fb.watch/test123')).toBe('facebook');
    });

    it('detects m.facebook.com URLs', () => {
      expect(getPlatform('https://m.facebook.com/video/test')).toBe('facebook');
      expect(getPlatform('http://m.facebook.com/video/test')).toBe('facebook');
    });
  });

  describe('Twitter detection', () => {
    it('detects twitter.com and x.com URLs', () => {
      expect(getPlatform('https://twitter.com/user/status/123')).toBe(
        'twitter',
      );
      expect(getPlatform('http://twitter.com/user/status/123')).toBe(
        'twitter',
      );
      expect(getPlatform('https://mobile.twitter.com/user/status/123')).toBe(
        'twitter',
      );
      expect(getPlatform('https://x.com/user/status/123')).toBe('twitter');
    });
  });

  describe('Threads detection', () => {
    it('detects threads.net URLs', () => {
      expect(getPlatform('https://threads.net/@user/post/test')).toBe('threads');
      expect(getPlatform('http://threads.net/@user/post/test')).toBe('threads');
      expect(getPlatform('https://www.threads.net/@user/post/test')).toBe('threads');
    });
  });

  describe('Reddit detection', () => {
    it('detects reddit.com URLs', () => {
      expect(getPlatform('https://reddit.com/r/test/comments/abc123')).toBe('reddit');
      expect(getPlatform('http://reddit.com/r/test/comments/abc123')).toBe('reddit');
      expect(getPlatform('https://www.reddit.com/r/test/comments/abc123')).toBe('reddit');
    });

    it('detects redd.it URLs', () => {
      expect(getPlatform('https://redd.it/abc123')).toBe('reddit');
      expect(getPlatform('http://redd.it/abc123')).toBe('reddit');
    });

    it('detects v.redd.it URLs', () => {
      expect(getPlatform('https://v.redd.it/abc123')).toBe('reddit');
      expect(getPlatform('http://v.redd.it/abc123')).toBe('reddit');
    });
  });

  describe('Unknown platform detection', () => {
    it('returns unknown for unsupported platforms', () => {
      expect(getPlatform('https://tiktok.com/@user/video/123')).toBe('unknown');
      expect(getPlatform('https://vimeo.com/123456789')).toBe('unknown');
      expect(getPlatform('https://example.com/video')).toBe('unknown');
    });

    it('returns unknown for invalid URLs', () => {
      expect(getPlatform('not-a-url')).toBe('unknown');
      expect(getPlatform('invalid://url')).toBe('unknown');
      expect(getPlatform('')).toBe('unknown');
      expect(getPlatform(' ')).toBe('unknown');
      expect(getPlatform('http://')).toBe('unknown');
      expect(getPlatform('ftp://example.com')).toBe('unknown');
    });
  });

  describe('Case insensitivity', () => {
    it('handles mixed case hostnames', () => {
      expect(getPlatform('https://YouTube.com/watch?v=test')).toBe('youtube');
      expect(getPlatform('https://INSTAGRAM.COM/p/test')).toBe('instagram');
      expect(getPlatform('https://Facebook.com/video/test')).toBe('facebook');
      expect(getPlatform('https://THREADS.NET/@user/post/test')).toBe('threads');
      expect(getPlatform('https://Reddit.com/r/test')).toBe('reddit');
      expect(getPlatform('https://TWITTER.COM/user/status/123')).toBe(
        'twitter',
      );
    });
  });

  describe('URL parsing edge cases', () => {
    it('handles URLs with query parameters and fragments', () => {
      expect(getPlatform('https://youtube.com/watch?v=test&t=10s#comment')).toBe('youtube');
      expect(getPlatform('https://instagram.com/p/test/?utm_source=ig_web_copy_link')).toBe('instagram');
      expect(getPlatform('https://facebook.com/video/test?ref=share#comments')).toBe('facebook');
    });

    it('handles URLs with paths', () => {
      expect(getPlatform('https://youtube.com/channel/UC123/videos')).toBe('youtube');
      expect(getPlatform('https://instagram.com/stories/user/123')).toBe('instagram');
      expect(getPlatform('https://reddit.com/r/programming/comments/abc/def/')).toBe('reddit');
    });

    it('handles URLs with ports', () => {
      expect(getPlatform('https://youtube.com:443/watch?v=test')).toBe('youtube');
      expect(getPlatform('http://instagram.com:80/p/test')).toBe('instagram');
    });
  });
}); 