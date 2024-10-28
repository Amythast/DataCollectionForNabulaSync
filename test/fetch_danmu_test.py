from danmu_fetcher import KuaishouDanmuFetcher, DouyinDanmuFetcher

if __name__ == '__main__':
    # live_id = 'Kslala666'
    # file_path = '/Users/feifeixia/LocalDesktop/GitHub/DataCollectionForNabulaSync/downloads'
    # cookie = '_did=web_282292274B62FBF0; did=web_d2bbcbdc52c37f9e4880818992ad817f289c; userId=3951625966'
    # KuaishouDanmuFetcher(live_id, file_path, 30, cookie).start()

    DouyinDanmuFetcher('169445216270', '//downloads', 30).start()