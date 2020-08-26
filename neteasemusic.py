import json
import requests
import re
from time import sleep
from pagermaid.listener import listener
from pagermaid import bot
from pagermaid.utils import obtain_message
from os import remove, path
from collections import defaultdict


@listener(is_plugin=True, outgoing=True, command="nem",
          description="网易云搜/点歌。",
          parameters="<指令> <关键词>")
async def nem(context):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}
    if len(context.parameter) < 2:
        await context.edit("使用方法：`-nem` `<指令>` `<关键词>`\n(指令s为搜索，指令p为播放\n关键词可填歌曲ID，或直接回复搜索结果 `-nem` `p` `<歌曲数字序号>`)")
        return
    else:
        keyword = ''
        for i in range(1, len(context.parameter)):
            keyword += context.parameter[i] + " "
    keyword = keyword[:-1]
    if context.parameter[0] == "s":  # 搜索功能
        await context.edit("搜索中 . . .")
        url = "http://music.163.com/api/search/pc?&s=" + \
            keyword + "&offset=0&limit=5&type=1"
        for _ in range(20):  # 最多尝试20次
            status = False
            req = requests.request("GET", url, headers=headers)
            if req.status_code == 200:
                req = json.loads(req.content)
                if req['result']:
                    info = defaultdict()
                    for i in range(len(req['result']['songs'])):
                        info[i] = {'id': '', 'title': '', 'alias': '',
                                   'album': '', 'albumpic': '', 'artist': ''}
                        info[i]['id'] = req['result']['songs'][i]['id']
                        info[i]['title'] = req['result']['songs'][i]['name']
                        info[i]['alias'] = req['result']['songs'][i]['alias']
                        info[i]['album'] = req['result']['songs'][i]['album']['name']
                        info[i]['albumpic'] = req['result']['songs'][i]['album']['picUrl']
                        for j in range(len(req['result']['songs'][i]['artists'])):
                            info[i]['artist'] += req['result']['songs'][i]['artists'][j]['name'] + " "
                    text = f"<strong>关于【{keyword}】的结果如下</strong> \n"
                    for i in range(len(info)):
                        text += f"#{i+1}： \n<strong>歌名</strong>： {info[i]['title']}\n"
                        if info[i]['alias']:
                            text += f"<strong>别名</strong>： {info[i]['alias'][0]} \n"
                        if info[i]['album']:
                            res = '<a href="' + \
                                info[i]['albumpic'] + '">' + \
                                info[i]['album'] + '</a>'
                            text += f"<strong>专辑</strong>： {res} \n"
                        text += f"<strong>作者</strong>： {info[i]['artist']}\n<strong>歌曲ID</strong>： <code>{info[i]['id']}</code>\n————————\n"
                    text += "回复此消息 <code>-nem p <歌曲序号></code> 即可点歌"
                    await context.edit(text, parse_mode='html', link_preview=True)
                    status = True
                    break
                else:
                    await context.edit("**未搜索到结果**")
                    status = True
                    break
            else:
                continue
        if status is False:
            await context.edit("出错了呜呜呜 ~ 试了好多好多次都无法访问到 API 服务器 。")
            sleep(2)
            await context.delete()
        return

    if context.parameter[0] == "p":  # 播放功能
        try:
            reply = await context.get_reply_message()
        except ValueError:
            await context.edit("出错了呜呜呜 ~ 无效的参数。")
            return
        search = ""
        title = ""
        if reply:
            msg = reply.message
            search = re.findall(".*【(.*)】.*", msg)
            if search:
                try:
                    if int(context.parameter[1]) > 5:
                        await context.edit("出错了呜呜呜 ~ 无效的歌曲序号。")
                        return
                    else:
                        start = "#" + context.parameter[1] + "："
                        search = ".*" + start + "(.*?)" + '————————' + ".*"
                        msg = re.findall(search, msg, re.S)[0]
                        search = ".*歌曲ID： (.*)\n.*"
                        title = ".*歌名： (.*?)\n.*"
                        title = "【"+re.findall(title, msg, re.S)[0]+"】"
                        keyword = re.findall(search, msg, re.S)[0]
                        if reply.sender.is_self:
                            await reply.edit(f"{title}点歌完成")
                except:
                    await context.edit("出错了呜呜呜 ~ 无效的参数。")
                    return
            else:
                await context.edit("出错了呜呜呜 ~ 无效的参数。")
                return

        await context.edit("获取中 . . .")
        try:
            import eyed3
            imported = True
        except ImportError:
            imported = False
            await bot.send_message(context.chat_id, '(`eyeD3`支持库未安装，歌曲文件信息将无法导入\n请使用 `-sh` `pip3` `install` `eyed3` 安装，或自行ssh安装)')
        url = "http://music.163.com/api/search/pc?&s=" + \
            keyword + "&offset=0&limit=1&type=1"
        for _ in range(20):  # 最多尝试20次
            status = False
            req = requests.request("GET", url, headers=headers)
            if req.status_code == 200:
                req = json.loads(req.content)
                if req['result']:
                    info = {'id': '', 'title': '', 'alias': '',
                            'album': '', 'albumpic': '', 'artist': ''}
                    info['id'] = req['result']['songs'][0]['id']
                    info['title'] = req['result']['songs'][0]['name']
                    info['alias'] = req['result']['songs'][0]['alias']
                    info['album'] = req['result']['songs'][0]['album']['name']
                    info['albumpic'] = req['result']['songs'][0]['album']['picUrl']
                    for j in range(len(req['result']['songs'][0]['artists'])):
                        info['artist'] += req['result']['songs'][0]['artists'][j]['name'] + ";"
                    info['artist'] = info['artist'][:-1]
                    if title:
                        title = ""
                    else:
                        title = f"【{info['title']}】"
                    await context.edit(f"{title}下载中 . . .")
                    # 下载
                    music = requests.request(
                        "GET", "http://music.163.com/song/media/outer/url?id=" + str(info['id']) + ".mp3", headers=headers)
                    name = info['title'].replace('/', " ") + ".mp3"
                    cap = info['artist'].replace(
                        ';', ', ') + " - " + "**" + info['title'] + "**"
                    pic = requests.get(info['albumpic'])
                    with open(name, 'wb') as f:
                        f.write(music.content)
                        if (path.getsize(name) / 1024) < 100:
                            remove(name)
                            try:
                                if reply.sender.is_self:
                                    await reply.delete()
                            except:
                                pass
                            await context.delete()
                            res = '你可以点击<a href="https://music.163.com/#/song?id=' + \
                                str(info['id']) + '">' + \
                                ' <strong>这里</strong> ' + '</a>' + '前往网页版收听'
                            await bot.send_message(context.chat_id, f"<strong>【{info['title']}】</strong>\n" + "歌曲获取失败，可能歌曲为VIP专属，或受到地区版权限制。\n" + res, parse_mode='html', link_preview=True)
                            return
                        if imported is True:
                            tag = eyed3.load(name).tag
                            tag.artist = info['artist']
                            tag.title = info['title']
                            tag.album = info['album']
                            tag.images.set(3, pic.content, "image/jpeg", u'')
                            tag.save(
                                version=eyed3.id3.ID3_DEFAULT_VERSION, encoding='utf-8')
                        await context.edit(f"{title}上传中 . . .")
                        await context.client.send_file(
                            context.chat_id,
                            name,
                            caption=cap,
                            link_preview=False,
                            force_document=False)
                        try:
                            if reply.sender.is_self:
                                await reply.delete()
                        except:
                            pass
                    try:
                        remove(name)
                    except:
                        pass
                    await context.delete()
                    status = True
                    break
                else:
                    await context.edit("**未搜索到结果**")
                    status = True
                    break
            else:
                continue

        if status is False:
            await context.edit("出错了呜呜呜 ~ 试了好多好多次都无法访问到 API 服务器 。")
            sleep(2)
            await context.delete()
