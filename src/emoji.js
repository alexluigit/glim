import fs from 'fs'
import { gemoji } from 'gemoji'

let tmpl=`---
name: emoji
version: "${process.env.GEMOJI_VER}"
sort: by_weight
use_preset_vocabulary: true
...
`

for (const emoji of gemoji) {
  for (const name of emoji.names) {
    tmpl+=`\n${emoji.emoji}\t${name.replace(/_/g, '')}`
  }
}

fs.writeFile(`${process.env.PWD}/emoji.dict.yaml`, tmpl, {flag: 'w+'}, err => {
  if (err) {console.error(err); return; }
})
