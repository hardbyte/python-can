
def add_to_parser(parser):
    parser.add_argument("-c", "--channel", type=str, dest="channel",
                        help="""
                        If the CAN interface supports multiple channels, select which one
                        you are after here. For example on linux this might be 1
                        """, default='0')

    parser.add_argument("-b", "--bitrate", type=int, dest="bitrate",
                        help="CAN bus bitrate", default=1000000)

    parser.add_argument("--tseg1", type=int, dest="tseg1",
                        help="CAN bus tseg1", default=4)

    parser.add_argument("--tseg2", type=int, dest="tseg2",
                        help="CAN bus tseg2", default=3)

    parser.add_argument("--sjw", type=int, dest="sjw",
                        help="Synchronisation Jump Width decides the maximum number of time quanta that the controller can resynchronise every bit.",
                        default=1)

    parser.add_argument("-n", "--num_samples", type=int, dest="no_samp",
                        help="""Some CAN controllers can also sample each bit three times.
                                In this case, the bit will be sampled three quanta in a row,
                                with the last sample being taken in the edge between TSEG1 and TSEG2.

                                Three samples should only be used for relatively slow baudrates.""",
                        default=1)
