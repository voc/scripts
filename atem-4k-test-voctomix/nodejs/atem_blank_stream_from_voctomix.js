/***************************************************************************
authors: MaZderMind, thomic
license: MIT License, Abbreviation: MIT, see: voc_mit_license.txt

Copyright (c) 2014-2018 c3voc <voc@c3voc.de>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
***************************************************************************/

/******************************SETTINGS************************************
**************************please set them here*****************************/
const settings = {
    EncoderIP: "10.73.4.3",
    EncoderControlPort: 9999,
    AtemIP: "10.73.4.30"
};

var net = require('net');
var atemcli = require('applest-atem');

var atem = new atemcli();

atem.on('connect', function() {
	console.log('connected to atem');
});
atem.connect(settings.AtemIP);

var connection = net.createConnection({
	host: settings.EncoderIP,
        port: settings.EncoderControlPort,

//debug with changing port on specific encoder and following commandline
//sudo nc -v -l -p 12555
//	port: 12555, //debug port

	encoding: 'UTF-8',
});
connection.on('connect', function() {
	console.log('connected to voctomix');
});


connection.on('data', function(line) {
	line = line.trim();
	line = line.split(" ")

//	console.log(line);
	console.log(line[0]);
	
	command = line[0]
	args = line.splice(1)
	
//	console.log(args);
	console.log(args[0]);
	
	if(command != 'stream_status') {
		return;
	}

	if(args[0] == 'live') {
		console.log('-> live');

                //PreviewList see here: https://github.com/applest/node-applest-atem/blob/master/docs/specification.md
                //Cam on Button 2 from left = 2

		atem.changePreviewInput(1);
//		atem.changeUpstreamKeyState (0, false);
		atem.cutTransition();
	}
	else if(args[0] == 'blank') {
		console.log('-> blank');

                //PreviewList see here: https://github.com/applest/node-applest-atem/blob/master/docs/specification.md
                //Media1 = 3010

		atem.changePreviewInput(3010);
//		atem.changeUpstreamKeyState (0, false);
		atem.cutTransition();
	}
});
