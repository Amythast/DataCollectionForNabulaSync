from translate import Translator

from dan_mu_fetcher.liveMan import DouyinLiveWebFetcher

if __name__ == '__main__':
    # live_id = '459078129156'
    # DouyinLiveWebFetcher(live_id, "/Users/feifeixia/LocalDesktop/GitHub/DouyinLiveRecorder/downloads", 'xiaomi').start()
    translator = Translator(to_lang="en", from_lang="zh")

    wyw_text = '季姬寂，集鸡，鸡即棘鸡。棘鸡饥叽，季姬及箕稷济鸡。'
    wyw_text1 = '天元邓岗'
    translation = translator.translate(wyw_text1)

    print(translation)




