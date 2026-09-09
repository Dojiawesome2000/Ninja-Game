n_squares, start, magic = [int(i) for i in input().split()]

squares = [int(i) for i in input().split()]
past_poses = [start]
k = 0
pos = start
gaming = True
reason = ''
while gaming:
    new_pos = pos + squares[pos-1]
    k+=1
    if new_pos > n_squares:
        print("right")
        gaming = False
    elif new_pos <= 0:
        print("left")
        gaming = False
    elif new_pos in past_poses:
        print('cycle')
        gaming = False
    elif squares[new_pos-1] == magic:
        print('magic')
        gaming = False
    else:
        pos = new_pos
        past_poses.append(pos)
        
    print(f"pos: {pos},     val: {squares[pos-1]}")
        
print(k)