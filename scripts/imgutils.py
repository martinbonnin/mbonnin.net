#! /usr/bin/env python
import sys;
sys.dont_write_bytecode = True
import utils;
import tempfile;
import os;

def ensure_less_than_one_megapixel(_in, _out):
    print("less than 1MB")
    proc = utils.execute_shell("convert -resize \\@1000000\\> " + _in + " " + _out);
    if (proc.returncode != 0):
        print("could not convert " + _in +": " + proc.err + ":" + proc.out);
        sys.exit(1);
    
 
def generate_thumbnail(_in, _out_dir):
    # XXX: not nice but much faster if we have them generated already
    if (os.path.isfile(_out_dir + "/thumbnail_green.png")):
        return;
    
    _tmp_square = _out_dir + "/tmp_square.png" #tempfile.mkstemp(suffix=".png", prefix="mbonnin.net")[1];
    _tmp_round = _out_dir + "/tmp_round.png" #tempfile.mkstemp(suffix=".png", prefix="mbonnin.net")[1];
    _tmp_round_bw = _out_dir + "/tmp_round_bw.png" #tempfile.mkstemp(suffix=".png", prefix="mbonnin.net")[1];

    # make input square
    command = "convert -resize 256x256^ -gravity center -extent 256x256 " + _in + " " + _tmp_square;
    print("executing " + command)
    proc = utils.execute_shell(command);
    if (proc.returncode != 0):
        utils.fatal("could not square thumbnail " + _in +": " + proc.err);

    # clip
    print("clipping")
    proc = utils.execute_shell("convert -colorspace sRGB " + in_dir + "/thumbnail_clip_mask.png " + _tmp_square + " -compose src-in -composite " + _tmp_round);
    if (proc.returncode != 0):
        utils.fatal("could not generate_thumbnail " + _in +": " + proc.err);

    # desaturate
    desaturate(_tmp_round, _tmp_round_bw);
    
    for color in ["green", "yellow"]:
        for bw in ["", "_bw"]:
            if (bw == "_bw"):
                r = _tmp_round_bw;
            else:
                r = _tmp_round;
            _out = _out_dir + "/thumbnail_" + color + bw + ".png";
            print("colorspace")
            print("convert -colorspace sRGB " + in_dir + "/thumbnail_border_" + color + ".png " + r + " -composite " + _out)
            proc = utils.execute_shell("convert -colorspace sRGB " + in_dir + "/thumbnail_border_" + color + ".png " + r + " -composite " + _out);
            if (proc.returncode != 0):
                utils.fatal("could not generate_thumbnail " + _in +": " + proc.err);
    
    #os.remove(_tmp_square);
    #os.remove(_tmp_round);
    #os.remove(_tmp_round_bw);

def init(_in):
    global in_dir;
    in_dir = _in;
    
def desaturate(_in, _out):
    print("desaturate")
    proc = utils.execute_shell("convert " + _in + " -colorspace Gray " + _out);
    if (proc.returncode != 0):
        utils.fatal("could not desaturate " + _in +": " + proc.err);
