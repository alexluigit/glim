import fs from 'fs'
import {gemoji} from 'gemoji'

const date = new Date().toISOString().split('T')[0];
let tmpl=`---
name: gemoji
version: "${date}"
sort: by_weight
use_preset_vocabulary: true
...
`
for (const emoji of gemoji) {
  for (const name of emoji.names) {
    tmpl+=`\n${emoji.emoji}\t;${name.replace(/_/g, '')}`
  }
}

fs.writeFile(`/home/${process.env.USER}/.local/share/fcitx5/rime/emoji.dict.yaml`, tmpl, {flag: 'w+'}, err => {
  if (err) {
    console.error(err)
    return
  }
})
