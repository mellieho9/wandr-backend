import pyktok as pyk
import pandas as pd
import os
from pathlib import Path

class TikTokDownloader:
    """
    TikTok video downloader using pyktok
    """
    
    def __init__(self, browser='chrome'):
        """Initialize the downloader with specified browser"""
        self.browser = browser
        pyk.specify_browser(browser)
        print(f"✅ TikTok downloader initialized with {browser}")
    
    def download_video(self, url, output_dir=".", metadata_file=None):
        """
        Download TikTok video and metadata
        
        Args:
            url: TikTok URL to download
            output_dir: Directory to save the video
            metadata_file: Optional CSV file to save metadata
            
        Returns:
            Dictionary with download results
        """
        try:
            print(f"📥 Downloading TikTok video: {url}")
            
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Save current directory and change to output directory
            # since pyktok downloads to current working directory
            original_cwd = os.getcwd()
            os.chdir(output_dir)
            
            try:
                # Download video and metadata
                if metadata_file:
                    # For metadata file, use relative path from output_dir
                    metadata_filename = os.path.basename(metadata_file)
                    pyk.save_tiktok(url, True, metadata_filename)
                else:
                    pyk.save_tiktok(url, True)
            finally:
                # Always return to original directory
                os.chdir(original_cwd)
            
            print(f"✅ Successfully downloaded: {url}")
            
            return {
                'url': url,
                'success': True,
                'output_dir': output_dir,
                'metadata_file': metadata_file
            }
            
        except Exception as e:
            error_msg = f"Error downloading {url}: {e}"
            print(f"❌ {error_msg}")
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    def download_multiple(self, urls, output_dir=".", category="tiktok"):
        """
        Download multiple TikTok videos
        
        Args:
            urls: List of TikTok URLs
            output_dir: Directory to save videos
            category: Category name for metadata file
            
        Returns:
            List of download results
        """
        results = []
        metadata_file = f"{category}_metadata.csv"
        
        print(f"📦 Downloading {len(urls)} TikTok videos...")
        
        for i, url in enumerate(urls, 1):
            print(f"\n🎬 Processing video {i}/{len(urls)}")
            result = self.download_video(url, output_dir, metadata_file)
            results.append(result)
        
        # Summary
        successful = len([r for r in results if r['success']])
        print(f"\n📊 Download Summary: {successful}/{len(urls)} successful")
        
        return results

# Example usage and testing
if __name__ == "__main__":
    downloader = TikTokDownloader()
    
    # Example URL
    test_url = "https://www.tiktok.com/t/ZP8rwYBo3/"
    
    # Download single video
    result = downloader.download_video(test_url, "downloads", "test_metadata.csv")
    print(f"Download result: {result}")
