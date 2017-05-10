class Node(object):
    """A node in the suffix tree. 
    
    suffix_node
        the index of a node with a matching suffix, representing a suffix link.
        -1 indicates this node has no suffix link.
    """
    def __init__(self):
        self.suffix_node = -1   

    def __repr__(self):
        return "Node(suffix link: %d)" % self.suffix_node

class Edge(object):
    """An edge in the suffix tree.
    
    first_obj_index
        index of start of sequence part represented by this edge
        
    last_obj_index
        index of end of sequence part represented by this edge
        
    source_node_index
        index of source node of edge
    
    dest_node_index
        index of destination node of edge
    """
    def __init__(self, first_obj_index, last_obj_index, source_node_index, dest_node_index):
        self.first_obj_index = first_obj_index
        self.last_obj_index = last_obj_index
        self.source_node_index = source_node_index
        self.dest_node_index = dest_node_index
        
    @property
    def length(self):
        return self.last_obj_index - self.first_obj_index

    def __repr__(self):
        return 'Edge(%d, %d, %d, %d)'% (self.source_node_index, self.dest_node_index 
                                        ,self.first_obj_index, self.last_obj_index )


class Suffix(object):
    """Represents a suffix from first_obj_index to last_obj_index.
    
    source_node_index
        index of node where this suffix starts
    
    first_obj_index
        index of start of suffix in the object sequence
        
    last_obj_index
        index of end of suffix in object sequence
    """
    def __init__(self, source_node_index, first_obj_index, last_obj_index):
        self.source_node_index = source_node_index
        self.first_obj_index = first_obj_index
        self.last_obj_index = last_obj_index
        
    @property
    def length(self):
        return self.last_obj_index - self.first_obj_index
                
    def explicit(self):
        """A suffix is explicit if it ends on a node. first_obj_index
        is set greater than last_obj_index to indicate this.
        """
        return self.first_obj_index > self.last_obj_index
    
    def implicit(self):
        return self.last_obj_index >= self.first_obj_index

        
class SuffixTree(object):
    """A suffix tree for string matching. Uses Ukkonen's algorithm
    for construction.
    """
    def __init__(self, seq):
        """
        seq 
            the sequence for which to construct a suffix tree
        """
        self.seq = seq
        self.N = len(seq) - 1
        self.nodes = [Node()]
        self.edges = {}
        self.active = Suffix(0, 0, -1)
        for i in range(len(seq)):
            self._add_prefix(i)
    
    def __repr__(self):
        """ 
        Lists edges in the suffix tree
        """
        curr_index = self.N
        s = "\tStart \tEnd \tSuf \tFirst \tLast \tString\n"
        values = list(self.edges.values())
        values.sort(key=lambda x: x.source_node_index)
        for edge in values:
            if edge.source_node_index == -1:
                continue
            s += "\t%s \t%s \t%s \t%s \t%s \t" % (edge.source_node_index,
                    edge.dest_node_index,
                    self.nodes[edge.dest_node_index].suffix_node,
                    edge.first_obj_index,
                    edge.last_obj_index)
            
            top = min(curr_index, edge.last_obj_index)
            s += str(self.seq[edge.first_obj_index:top+1]) + "\n"
        return s
            
    def _add_prefix(self, last_obj_index):
        """The core construction method.
        """
        last_parent_node = -1
        while True:
            parent_node = self.active.source_node_index
            if self.active.explicit():
                if (self.active.source_node_index, self.seq[last_obj_index]) in self.edges:
                    # prefix is already in tree
                    break
            else:
                e = self.edges[self.active.source_node_index, self.seq[self.active.first_obj_index]]
                if self.seq[e.first_obj_index + self.active.length + 1] == self.seq[last_obj_index]:
                    # prefix is already in tree
                    break
                parent_node = self._split_edge(e, self.active)
        

            self.nodes.append(Node())
            e = Edge(last_obj_index, self.N, parent_node, len(self.nodes) - 1)
            self._insert_edge(e)
            
            if last_parent_node > 0:
                self.nodes[last_parent_node].suffix_node = parent_node
            last_parent_node = parent_node
            
            if self.active.source_node_index == 0:
                self.active.first_obj_index += 1
            else:
                self.active.source_node_index = self.nodes[self.active.source_node_index].suffix_node
            self._canonize_suffix(self.active)
        if last_parent_node > 0:
            self.nodes[last_parent_node].suffix_node = parent_node
        self.active.last_obj_index += 1
        self._canonize_suffix(self.active)
        
    def _insert_edge(self, edge):
        self.edges[(edge.source_node_index, self.seq[edge.first_obj_index])] = edge
        
    def _remove_edge(self, edge):
        self.edges.pop((edge.source_node_index, self.seq[edge.first_obj_index]))
        
    def _split_edge(self, edge, suffix):
        self.nodes.append(Node())
        e = Edge(edge.first_obj_index, edge.first_obj_index + suffix.length, suffix.source_node_index, len(self.nodes) - 1)
        self._remove_edge(edge)
        self._insert_edge(e)
        self.nodes[e.dest_node_index].suffix_node = suffix.source_node_index  ### need to add node for each edge
        edge.first_obj_index += suffix.length + 1
        edge.source_node_index = e.dest_node_index
        self._insert_edge(edge)
        return e.dest_node_index

    def _canonize_suffix(self, suffix):
        """This canonizes the suffix, walking along its suffix string until it 
        is explicit or there are no more matched nodes.
        """
        if not suffix.explicit():
            e = self.edges[suffix.source_node_index, self.seq[suffix.first_obj_index]]
            if e.length <= suffix.length:
                suffix.first_obj_index += e.length + 1
                suffix.source_node_index = e.dest_node_index
                self._canonize_suffix(suffix)
 

    # Public methods
    def find_substring(self, substring):
        """Returns the index of substring in string or -1 if it
        is not found.
        """
        if not substring:
            return -1
        if self.case_insensitive:
            substring = substring.lower()
        curr_node = 0
        i = 0
        while i < len(substring):
            edge = self.edges.get((curr_node, substring[i]))
            if not edge:
                return -1
            ln = min(edge.length + 1, len(substring) - i)
            if substring[i:i + ln] != self.string[edge.first_obj_index:edge.first_obj_index + ln]:
                return -1
            i += edge.length + 1
            curr_node = edge.dest_node_index
        return edge.first_obj_index - len(substring) + ln
        
    def has_substring(self, substring):
        return self.find_substring(substring) != -1
