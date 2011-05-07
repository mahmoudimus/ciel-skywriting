(*
 * Copyright (c) 2011 Anil Madhavapeddy <anil@recoil.org>
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *)


open Printf
open Lwt
open Yojson

let parse_args () =
  match Sys.argv with
    | [| _; "--write-fifo"; wf; "--read-fifo"; rf |]
    | [| _; "--read-fifo"; rf; "--write-fifo"; wf |] ->
      (rf, wf)
    | _ ->
      failwith (sprintf "Unable to parse cmdline args: %s"
        (String.concat " " (Array.to_list Sys.argv)))

let main () =
  Sys.set_signal Sys.sigpipe Sys.Signal_ignore;
  let rf, wf = parse_args () in
  lwt wfd = Lwt_unix.openfile wf [Unix.O_WRONLY] 0 in
  lwt rfd = Lwt_unix.openfile rf [Unix.O_RDONLY] 0 in
  Cmd.fifo_t wfd rfd
 
let _ = 
  Lwt_main.run (main ())
